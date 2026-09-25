"""Registry of document versions, ingestion runs, corpus versions, aliases and gate reports.

The registry is the source of truth for versions. It runs on Postgres in every environment and on
SQLite in unit tests.
"""

import uuid
from collections.abc import Collection, Mapping
from typing import Any

from sqlalchemy import Engine, func, insert, select, update

from chatbot_contracts.corpus import CorpusManifest, DocumentVersion
from chatbot_contracts.enums import CorpusStatus
from chatbot_platform import sql
from chatbot_platform.errors import NotFoundError
from chatbot_platform.models import CheckResult, GateReport, RunStatus, SmeDecision

_DOC_FIELDS = tuple(DocumentVersion.model_fields)


class Registry:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def create_tables(self) -> None:
        """Create the registry and ops tables. Postgres uses migrations instead, see migrate.py."""
        sql.metadata.create_all(self.engine)

    # Document versions

    def add_doc_version(self, doc: DocumentVersion) -> None:
        row = doc.model_dump(include=set(_DOC_FIELDS) - {"schema_version"})
        row["created_at"] = sql.utcnow()
        with self.engine.begin() as conn:
            conn.execute(insert(sql.doc_versions).values(row))

    def get_doc_version(self, doc_version: str) -> DocumentVersion:
        found = self.doc_versions_by_id([doc_version])
        if doc_version not in found:
            raise NotFoundError(f"unknown document version {doc_version}")
        return found[doc_version]

    def doc_versions_by_id(self, doc_versions: Collection[str]) -> dict[str, DocumentVersion]:
        query = select(sql.doc_versions).where(sql.doc_versions.c.doc_version.in_(doc_versions))
        with self.engine.connect() as conn:
            rows = conn.execute(query).mappings().all()
        return {row["doc_version"]: _doc_from_row(row) for row in rows}

    def find_doc_version(self, doc_id: str, sha256: str) -> DocumentVersion | None:
        table = sql.doc_versions
        query = select(table).where(table.c.doc_id == doc_id, table.c.sha256 == sha256)
        with self.engine.connect() as conn:
            row = conn.execute(query).mappings().first()
        return _doc_from_row(row) if row else None

    def latest_doc_version(self, doc_id: str) -> DocumentVersion | None:
        """Newest version of a document that is not retracted."""
        table = sql.doc_versions
        query = (
            select(table)
            .where(table.c.doc_id == doc_id, table.c.retracted_at.is_(None))
            .order_by(table.c.created_at.desc())
            .limit(1)
        )
        with self.engine.connect() as conn:
            row = conn.execute(query).mappings().first()
        return _doc_from_row(row) if row else None

    def set_page_count(self, doc_version: str, page_count: int) -> None:
        self._update_one(
            sql.doc_versions, sql.doc_versions.c.doc_version, doc_version, page_count=page_count
        )

    def retract(self, doc_version: str) -> None:
        self._update_one(
            sql.doc_versions, sql.doc_versions.c.doc_version, doc_version, retracted_at=sql.utcnow()
        )

    def superseded_by(self, doc_versions: Collection[str]) -> dict[str, str]:
        """Old version to the version that corrects it, for the given old versions."""
        table = sql.doc_versions
        query = select(table.c.supersedes, table.c.doc_version).where(
            table.c.supersedes.in_(doc_versions)
        )
        with self.engine.connect() as conn:
            return {old: new for old, new in conn.execute(query)}

    def retracted(self, doc_versions: Collection[str]) -> set[str]:
        table = sql.doc_versions
        query = select(table.c.doc_version).where(
            table.c.doc_version.in_(doc_versions), table.c.retracted_at.is_not(None)
        )
        with self.engine.connect() as conn:
            return set(conn.execute(query).scalars())

    # Ingestion runs

    def start_run(self, doc_version: str, dagster_run_id: str | None = None) -> str:
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        row = {
            "run_id": run_id,
            "doc_version": doc_version,
            "dagster_run_id": dagster_run_id,
            "status": RunStatus.RUNNING,
            "started_at": sql.utcnow(),
            "worker_digests": {},
            "model_versions": {},
        }
        with self.engine.begin() as conn:
            conn.execute(insert(sql.ingestion_runs).values(row))
        return run_id

    def finish_run(
        self,
        run_id: str,
        status: RunStatus,
        worker_digests: Mapping[str, str] | None = None,
        model_versions: Mapping[str, str] | None = None,
    ) -> None:
        self._update_one(
            sql.ingestion_runs,
            sql.ingestion_runs.c.run_id,
            run_id,
            status=status,
            finished_at=sql.utcnow(),
            worker_digests=dict(worker_digests or {}),
            model_versions=dict(model_versions or {}),
        )

    def pending_doc_versions(self) -> list[str]:
        """Registered versions without a successful ingestion run. The Dagster sensor reads it."""
        docs, runs = sql.doc_versions, sql.ingestion_runs
        done = select(runs.c.doc_version).where(runs.c.status == RunStatus.SUCCEEDED)
        query = (
            select(docs.c.doc_version)
            .where(docs.c.retracted_at.is_(None), docs.c.doc_version.not_in(done))
            .order_by(docs.c.created_at)
        )
        with self.engine.connect() as conn:
            return list(conn.execute(query).scalars())

    # Corpus versions and aliases

    def next_version_id(self) -> int:
        with self.engine.connect() as conn:
            current = conn.execute(select(func.max(sql.corpus_versions.c.version_id))).scalar()
        return (current or 0) + 1

    def add_corpus_version(self, manifest: CorpusManifest) -> None:
        row = manifest.model_dump(exclude={"schema_version", "producer"})
        row["created_at"] = sql.utcnow()
        with self.engine.begin() as conn:
            conn.execute(insert(sql.corpus_versions).values(row))

    def get_corpus_version(self, version_id: int) -> CorpusManifest:
        query = select(sql.corpus_versions).where(sql.corpus_versions.c.version_id == version_id)
        with self.engine.connect() as conn:
            row = conn.execute(query).mappings().first()
        if row is None:
            raise NotFoundError(f"unknown corpus version {version_id}")
        return _manifest_from_row(row)

    def list_corpus_versions(self) -> list[CorpusManifest]:
        query = select(sql.corpus_versions).order_by(sql.corpus_versions.c.version_id)
        with self.engine.connect() as conn:
            return [_manifest_from_row(row) for row in conn.execute(query).mappings()]

    def latest_published(self) -> CorpusManifest | None:
        table = sql.corpus_versions
        query = (
            select(table)
            .where(table.c.status == CorpusStatus.PUBLISHED)
            .order_by(table.c.version_id.desc())
            .limit(1)
        )
        with self.engine.connect() as conn:
            row = conn.execute(query).mappings().first()
        return _manifest_from_row(row) if row else None

    def set_corpus_status(
        self, version_id: int, status: CorpusStatus, gate_report_id: str | None = None
    ) -> None:
        values: dict[str, Any] = {"status": status}
        if gate_report_id is not None:
            values["gate_report_id"] = gate_report_id
        if status == CorpusStatus.PUBLISHED:
            values["published_at"] = sql.utcnow()
        self._update_one(
            sql.corpus_versions, sql.corpus_versions.c.version_id, version_id, **values
        )

    def get_alias(self, name: str) -> int | None:
        query = select(sql.corpus_aliases.c.version_id).where(sql.corpus_aliases.c.name == name)
        with self.engine.connect() as conn:
            return conn.execute(query).scalar()

    def set_alias(self, name: str, version_id: int) -> None:
        table = sql.corpus_aliases
        with self.engine.begin() as conn:
            moved = conn.execute(
                update(table)
                .where(table.c.name == name)
                .values(version_id=version_id, updated_at=sql.utcnow())
            ).rowcount
            if not moved:
                conn.execute(
                    insert(table).values(name=name, version_id=version_id, updated_at=sql.utcnow())
                )

    # Gate reports

    def add_gate_report(self, report: GateReport) -> None:
        row = report.model_dump()
        with self.engine.begin() as conn:
            conn.execute(insert(sql.gate_reports).values(row))

    def get_gate_report(self, report_id: str) -> GateReport:
        query = select(sql.gate_reports).where(sql.gate_reports.c.report_id == report_id)
        with self.engine.connect() as conn:
            row = conn.execute(query).mappings().first()
        if row is None:
            raise NotFoundError(f"unknown gate report {report_id}")
        values = dict(row)
        values["checks"] = [CheckResult(**check) for check in values["checks"]]
        values["created_at"] = sql.as_utc(values["created_at"])
        values["sme_at"] = sql.as_utc(values["sme_at"])
        return GateReport(**values)

    def set_sme_decision(
        self, report_id: str, decision: SmeDecision, by: str, comment: str | None
    ) -> None:
        self._update_one(
            sql.gate_reports,
            sql.gate_reports.c.report_id,
            report_id,
            sme_decision=decision,
            sme_by=by,
            sme_comment=comment,
            sme_at=sql.utcnow(),
        )

    def _update_one(self, table, key_column, key: object, **values: Any) -> None:
        with self.engine.begin() as conn:
            changed = conn.execute(update(table).where(key_column == key).values(**values)).rowcount
        if changed != 1:
            raise NotFoundError(f"no row in {table.name} with key {key}")


def _doc_from_row(row: Mapping[str, Any]) -> DocumentVersion:
    return DocumentVersion(**{field: row[field] for field in _DOC_FIELDS if field in row})


def _manifest_from_row(row: Mapping[str, Any]) -> CorpusManifest:
    fields = set(CorpusManifest.model_fields) - {"schema_version", "producer"}
    return CorpusManifest(**{field: row[field] for field in fields})
