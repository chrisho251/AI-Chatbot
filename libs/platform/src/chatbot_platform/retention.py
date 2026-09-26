"""Retention sweep. The pipeline lane runs it daily from Dagster.

Every table lives in Postgres, so each rule deletes or blanks rows in place and nothing survives
in an older snapshot. Uploads are student data with the shortest TTL. Student free text in ops
rows, the encrypted question and the answer, is blanked after the text TTL. Operational rows are
deleted after the ops TTL. Staged chunk sets are deleted after the staging TTL, because published
chunks already live in serving.chunks.
Database backups must not outlive the ops TTL, otherwise a restore brings deleted rows back.
Destroying old key epochs is part of the security lane, see chatbot_common.keys.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import Engine, delete, select, update

from chatbot_platform import sql
from chatbot_platform.settings import PlatformSettings
from chatbot_platform.storage import ObjectStore, split_uri


@dataclass(frozen=True)
class RetentionResult:
    target: str
    deleted: int


def expire_uploads(engine: Engine, store: ObjectStore, cutoff: datetime) -> RetentionResult:
    table = sql.uploads
    with engine.connect() as conn:
        old = conn.execute(
            select(table.c.attachment_id, table.c.uri).where(table.c.created_at < cutoff)
        ).all()
    for _, uri in old:
        store.delete(*split_uri(uri))
    with engine.begin() as conn:
        conn.execute(delete(table).where(table.c.attachment_id.in_([row[0] for row in old])))
    return RetentionResult("ops.uploads", len(old))


def blank_text(engine: Engine, cutoff: datetime) -> list[RetentionResult]:
    """Keep the facts of old requests and tickets, drop the student text they carry."""
    results = []
    with engine.begin() as conn:
        for table in (sql.interactions, sql.escalation_tickets):
            blanked = conn.execute(
                update(table)
                .where(table.c.created_at < cutoff, table.c.question_enc != "")
                .values(question_enc="", answer=None)
            ).rowcount
            results.append(RetentionResult(f"ops.{table.name} text", blanked))
    return results


def expire_ops(engine: Engine, cutoff: datetime) -> list[RetentionResult]:
    """Delete old interactions with their citations and tool calls, then the other ops rows."""
    interactions = sql.interactions
    old_requests = select(interactions.c.request_id).where(interactions.c.created_at < cutoff)
    results = []
    with engine.begin() as conn:
        request_ids = list(conn.execute(old_requests).scalars())
        for child in (sql.citations, sql.tool_calls):
            conn.execute(delete(child).where(child.c.request_id.in_(request_ids)))
        conn.execute(delete(interactions).where(interactions.c.request_id.in_(request_ids)))
        results.append(RetentionResult("ops.interactions", len(request_ids)))
        for table, column in (
            (sql.escalation_tickets, sql.escalation_tickets.c.created_at),
            (sql.request_facts, sql.request_facts.c.created_at),
            (sql.guard_events, sql.guard_events.c.created_at),
            (sql.conversations, sql.conversations.c.last_active_at),
        ):
            deleted = conn.execute(delete(table).where(column < cutoff)).rowcount
            results.append(RetentionResult(f"ops.{table.name}", deleted))
    return results


def expire_staging(engine: Engine, cutoff: datetime) -> RetentionResult:
    table = sql.staged_chunks
    with engine.begin() as conn:
        deleted = conn.execute(delete(table).where(table.c.created_at < cutoff)).rowcount
    return RetentionResult("ingest.chunks", deleted)


def run_retention(
    engine: Engine,
    store: ObjectStore,
    settings: PlatformSettings,
    now: datetime | None = None,
) -> list[RetentionResult]:
    now = now or sql.utcnow()
    return [
        expire_uploads(engine, store, now - timedelta(days=settings.retention_uploads_days)),
        *blank_text(engine, now - timedelta(days=settings.retention_text_days)),
        *expire_ops(engine, now - timedelta(days=settings.retention_ops_days)),
        expire_staging(engine, now - timedelta(days=settings.retention_staging_days)),
    ]
