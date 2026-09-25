from datetime import timedelta

from sqlalchemy import func, insert, select

from chatbot_platform import lake, sql
from chatbot_platform.retention import run_retention
from chatbot_platform.settings import UPLOADS_BUCKET


def _count(platform, table):
    with platform.engine.connect() as conn:
        return conn.execute(select(func.count()).select_from(table)).scalar()


def test_old_data_is_deleted_everywhere(platform):
    now = sql.utcnow()
    old, recent = now - timedelta(days=1000), now - timedelta(days=1)
    for key, created in (("old", old), ("recent", recent)):
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
                    request_id=key, pseudo_user="p", question_enc="c", created_at=created
                )
            )
            conn.execute(insert(sql.citations).values(request_id=key, chunk_id="chunk"))
    lake.append_rows(platform.catalog, "obs.guard_events", [{"ts": old}, {"ts": recent}])

    results = {
        r.target: r.deleted
        for r in run_retention(
            platform.engine, platform.store, platform.catalog, platform.settings, now=now
        )
    }

    assert results["ops.uploads"] == 1
    assert results["ops.interactions"] == 1
    assert results["obs.guard_events"] == 1
    assert platform.store.list_keys(UPLOADS_BUCKET) == ["2026/recent.jpg"]
    assert _count(platform, sql.interactions) == 1
    assert _count(platform, sql.citations) == 1
