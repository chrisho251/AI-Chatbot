"""Retention sweep. The pipeline lane runs it daily from Dagster.

Uploads are student data with the shortest TTL. Hot ops rows follow ops TTL. Iceberg history
tables follow history TTL, then their old snapshots are expired so time travel cannot bring deleted
rows back. Destroying pseudonym key epochs in Vault is part of the security lane, not this module.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from pyiceberg.catalog import Catalog
from sqlalchemy import Engine, delete, select

from chatbot_platform import lake, sql
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


def expire_ops(engine: Engine, cutoff: datetime) -> list[RetentionResult]:
    """Delete old interactions with their citations and tool calls, then old tickets."""
    interactions = sql.interactions
    old_requests = select(interactions.c.request_id).where(interactions.c.created_at < cutoff)
    with engine.begin() as conn:
        request_ids = list(conn.execute(old_requests).scalars())
        for child in (sql.citations, sql.tool_calls):
            conn.execute(delete(child).where(child.c.request_id.in_(request_ids)))
        conn.execute(delete(interactions).where(interactions.c.request_id.in_(request_ids)))
        tickets = conn.execute(
            delete(sql.escalation_tickets).where(sql.escalation_tickets.c.created_at < cutoff)
        ).rowcount
    return [
        RetentionResult("ops.interactions", len(request_ids)),
        RetentionResult("ops.escalation_tickets", tickets),
    ]


def expire_history(catalog: Catalog, cutoff: datetime, now: datetime) -> list[RetentionResult]:
    """Every snapshot taken before the delete still holds the deleted rows, so all of them go."""
    results = []
    for table, column in lake.TTL_COLUMNS.items():
        deleted = lake.delete_older_than(catalog, table, column, cutoff)
        if deleted:
            lake.expire_snapshots(catalog, table, now)
        results.append(RetentionResult(table, deleted))
    return results


def run_retention(
    engine: Engine,
    store: ObjectStore,
    catalog: Catalog,
    settings: PlatformSettings,
    now: datetime | None = None,
) -> list[RetentionResult]:
    now = now or sql.utcnow()
    return [
        expire_uploads(engine, store, now - timedelta(days=settings.retention_uploads_days)),
        *expire_ops(engine, now - timedelta(days=settings.retention_ops_days)),
        *expire_history(catalog, now - timedelta(days=settings.retention_history_days), now),
    ]
