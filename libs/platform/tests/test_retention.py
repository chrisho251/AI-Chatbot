from datetime import timedelta

from sqlalchemy import func, insert, select

from chatbot_contracts import samples
from chatbot_platform import ingest, sql
from chatbot_platform.retention import run_retention
from chatbot_platform.settings import UPLOADS_BUCKET


def _count(platform, table):
    with platform.engine.connect() as conn:
        return conn.execute(select(func.count()).select_from(table)).scalar()


def _rows(platform, now):
    """Rows at three ages, past every TTL, past the text TTL only, and recent."""
    ages = {"old": now - timedelta(days=1000), "mid": now - timedelta(days=500)}
    ages["recent"] = now - timedelta(days=1)
    for key, created in ages.items():
        uri = platform.store.put(UPLOADS_BUCKET, f"2026/{key}.jpg", b"photo")
        with platform.engine.begin() as conn:
            conn.execute(
                insert(sql.uploads).values(
                    attachment_id=key,
                    request_id=key,
                    media_type="image/jpeg",
                    uri=uri,
                    sha256="0" * 64,
                    size_bytes=5,
                    created_at=created,
                )
            )
            conn.execute(
                insert(sql.interactions).values(
                    request_id=key,
                    pseudo_user="p",
                    question_enc="ciphertext",
                    answer="answer",
                    created_at=created,
                )
            )
            conn.execute(insert(sql.citations).values(request_id=key, chunk_id="chunk"))
            conn.execute(
                insert(sql.guard_events).values(
                    request_id=key,
                    detector="injection",
                    stage="gateway",
                    category="jailbreak",
                    score=0.9,
                    action="block",
                    created_at=created,
                )
            )
            conn.execute(
                insert(sql.conversations).values(
                    conversation_id=key, pseudo_user="p", started_at=created, last_active_at=created
                )
            )


def test_old_data_is_deleted_and_old_text_is_blanked(platform):
    now = sql.utcnow()
    _rows(platform, now)
    ingest.write_chunk_set(platform.engine, samples.sample_chunk_set())

    results = {
        r.target: r.deleted
        for r in run_retention(platform.engine, platform.store, platform.settings, now=now)
    }

    assert results["ops.uploads"] == 2
    assert results["ops.interactions text"] == 2
    assert results["ops.interactions"] == 1
    assert results["ops.guard_events"] == 1
    assert results["ops.conversations"] == 1
    assert results["ingest.chunks"] == 0
    assert platform.store.list_keys(UPLOADS_BUCKET) == ["2026/recent.jpg"]
    assert _count(platform, sql.citations) == 2
    with platform.engine.connect() as conn:
        rows = conn.execute(
            select(sql.interactions.c.request_id, sql.interactions.c.question_enc)
        ).all()
    assert sorted(rows) == [("mid", ""), ("recent", "ciphertext")]


def test_staged_chunks_expire_after_the_staging_ttl(platform):
    ingest.write_chunk_set(platform.engine, samples.sample_chunk_set())
    days = platform.settings.retention_staging_days
    for offset, expected in ((days - 1, 0), (days + 1, len(samples.PAGE_TEXTS))):
        now = sql.utcnow() + timedelta(days=offset)
        results = run_retention(platform.engine, platform.store, platform.settings, now=now)
        assert {r.target: r.deleted for r in results}["ingest.chunks"] == expected
