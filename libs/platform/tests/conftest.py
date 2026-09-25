import os
from dataclasses import replace

import pytest

from chatbot_contracts import samples
from chatbot_contracts.enums import SourceType
from chatbot_platform.documents import register_document
from chatbot_platform.testing import make_test_platform

PG_URL_ENV = "PLATFORM_TEST_DATABASE_URL"


@pytest.fixture(params=["sqlite", pytest.param("postgres", marks=pytest.mark.integration)])
def platform(request, tmp_path):
    """The test platform, and with the integration marker the same tests on real Postgres."""
    test_platform = make_test_platform(tmp_path / "platform")
    if request.param == "sqlite":
        return test_platform
    from chatbot_platform.pg_index import PgServingIndex
    from chatbot_platform.registry import Registry

    engine = request.getfixturevalue("pg_engine")
    return replace(
        test_platform,
        engine=engine,
        registry=Registry(engine),
        index=PgServingIndex(engine, samples.EMBEDDING_DIM),
    )


@pytest.fixture(scope="session")
def pg_session_engine():
    """One connection for the whole run. Skips when no test database is configured."""
    url = os.environ.get(PG_URL_ENV)
    if not url:
        pytest.skip(f"set {PG_URL_ENV} to run Postgres tests")
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    engine = create_engine(url, poolclass=StaticPool)
    yield engine
    engine.dispose()


@pytest.fixture
def pg_engine(pg_session_engine):
    """Postgres with pgvector, reset and migrated to head before each test."""
    from chatbot_platform import migrate, sql

    with pg_session_engine.begin() as conn:
        for schema in sql.SCHEMAS:
            conn.exec_driver_sql(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        conn.exec_driver_sql("DROP TABLE IF EXISTS alembic_version")
        url = pg_session_engine.url.render_as_string(hide_password=False)
        migrate.upgrade(url, samples.EMBEDDING_DIM, connection=conn)
    return pg_session_engine


@pytest.fixture
def upload(platform):
    """Register a file and set its page count, like W1 does after layout analysis."""

    def _upload(content: bytes, source_id: str = samples.SOURCE_ID, **kwargs):
        document = register_document(
            platform.registry,
            platform.store,
            content,
            filename="chapter.pdf",
            course_code=samples.COURSE_CODE,
            source_id=source_id,
            source_type=kwargs.pop("source_type", SourceType.TEXTBOOK),
            **kwargs,
        )
        platform.registry.set_page_count(document.doc_version, len(samples.PAGE_TEXTS))
        return platform.registry.get_doc_version(document.doc_version)

    return _upload


@pytest.fixture
def ingest(platform):
    """Chunk, gate, approve and publish document versions, like the Dagster pipeline does.

    Pass a mapping of document version to page texts. Returns the published manifest.
    """
    from chatbot_platform.gate import GateContext, default_checks, record_sme_decision, run_gate
    from chatbot_platform.models import RunStatus
    from chatbot_platform.versioning import create_candidate, publish

    def _ingest(texts_by_doc: dict[str, list[str]], remove=(), embedding_model=None):
        registry = platform.registry
        chunk_sets, pages = [], []
        for doc_version, texts in texts_by_doc.items():
            registry.set_page_count(doc_version, len(texts))
            run_id = registry.start_run(doc_version)
            chunk_set = samples.sample_chunk_set(
                texts, doc_version=doc_version, ingestion_run_id=run_id
            )
            if embedding_model:
                chunk_set = rechunk(chunk_set, embedding_model)
            chunk_sets.append(chunk_set)
            pages += [
                samples.sample_clean_page(
                    doc_version=doc_version, page_no=page, ingestion_run_id=run_id
                )
                for page in range(1, len(texts) + 1)
            ]
            registry.finish_run(run_id, RunStatus.SUCCEEDED)
        manifest = create_candidate(
            registry,
            add=list(texts_by_doc),
            remove=remove,
            embedding_model=embedding_model or samples.EMBEDDING_MODEL,
            chunker_version=samples.CHUNKER_VERSION,
        )
        documents = registry.doc_versions_by_id(texts_by_doc)
        context = GateContext(manifest, chunk_sets, pages, documents)
        report = run_gate(registry, context, default_checks(platform.settings))
        if report.requires_sme:
            record_sme_decision(registry, report.report_id, approved=True, by="sme@example")
        return publish(registry, platform.index, manifest.version_id, chunk_sets)

    return _ingest


def rechunk(chunk_set, embedding_model: str):
    """Same chunks encoded with another embedding model, with ids recomputed."""
    from chatbot_contracts.ids import make_chunk_id

    chunks = [
        chunk.model_copy(
            update={
                "chunk_id": make_chunk_id(
                    chunk.doc_version,
                    chunk.page_start,
                    chunk.page_end,
                    chunk.text,
                    chunk_set.chunker_version,
                    embedding_model,
                )
            }
        )
        for chunk in chunk_set.chunks
    ]
    return chunk_set.model_copy(update={"chunks": chunks, "embedding_model": embedding_model})
