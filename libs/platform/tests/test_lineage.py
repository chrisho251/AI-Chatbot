from sqlalchemy import insert, select

from chatbot_contracts import samples
from chatbot_platform import sql
from chatbot_platform.lineage import sweep_superseded, trace_citation

TEXTS = list(samples.PAGE_TEXTS)


def _answer(platform, request_id, chunk_id):
    with platform.engine.begin() as conn:
        conn.execute(
            insert(sql.interactions).values(
                request_id=request_id,
                pseudo_user="pseudo-1",
                question_enc="ciphertext",
                created_at=sql.utcnow(),
            )
        )
        conn.execute(insert(sql.citations).values(request_id=request_id, chunk_id=chunk_id))


def test_trace_follows_a_citation_to_the_raw_file(platform, upload, ingest):
    document = upload(b"edition one")
    manifest = ingest({document.doc_version: TEXTS})
    chunk_id = next(iter(platform.index.active_chunks(manifest.version_id)))
    trace = trace_citation(platform.registry, platform.index, chunk_id)
    assert trace.doc_version == document.doc_version
    assert trace.raw_sha256 == document.sha256
    assert trace.raw_uri == document.raw_uri
    assert trace.ingestion_run_id.startswith("run-")


def test_sweep_flags_answers_that_cited_a_corrected_source(platform, upload, ingest):
    old = upload(b"edition one")
    first = ingest({old.doc_version: TEXTS})
    cited = next(iter(platform.index.active_chunks(first.version_id)))
    _answer(platform, "req-1", cited)

    assert sweep_superseded(platform.registry, platform.index) == []

    new = upload(b"edition two")
    ingest({new.doc_version: ["A corrected page."]})
    flags = sweep_superseded(platform.registry, platform.index)
    assert [(f.request_id, f.superseded_by) for f in flags] == [("req-1", new.doc_version)]

    with platform.engine.connect() as conn:
        corrected = conn.execute(select(sql.interactions.c.source_corrected)).scalar()
    assert corrected is True
    assert sweep_superseded(platform.registry, platform.index) == []
