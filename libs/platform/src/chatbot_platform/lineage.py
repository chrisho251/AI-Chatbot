"""Lineage from a citation back to the raw file, and the sweep that flags stale answers.

The trace follows citation, chunk, document version and pages, ingestion run, raw object.
The sweep finds past answers that cited a chunk whose document was corrected or retracted since,
flags them as source corrected and returns them so the pipeline can open SME tickets.
"""

from sqlalchemy import select, update

from chatbot_platform import sql
from chatbot_platform.errors import NotFoundError
from chatbot_platform.index import ServingIndex
from chatbot_platform.models import SERVING_ALIAS, CorrectionFlag, LineageTrace
from chatbot_platform.registry import Registry


def trace_citation(registry: Registry, index: ServingIndex, chunk_id: str) -> LineageTrace:
    stored = index.get_chunks([chunk_id])
    if not stored:
        raise NotFoundError(f"chunk {chunk_id} is not in the serving index")
    chunk = stored[0]
    document = registry.get_doc_version(chunk.chunk.doc_version)
    return LineageTrace(
        chunk_id=chunk_id,
        doc_version=document.doc_version,
        page_start=chunk.chunk.page_start,
        page_end=chunk.chunk.page_end,
        region_ids=chunk.chunk.region_ids,
        ingestion_run_id=chunk.ingestion_run_id,
        raw_sha256=document.sha256,
        raw_uri=document.raw_uri,
        source_url=document.source_url,
        licence=document.licence,
    )


def sweep_superseded(registry: Registry, index: ServingIndex) -> list[CorrectionFlag]:
    serving = registry.get_alias(SERVING_ALIAS)
    if serving is None:
        return []
    interactions, citations = sql.interactions, sql.citations
    query = (
        select(citations.c.request_id, citations.c.chunk_id)
        .join(interactions, interactions.c.request_id == citations.c.request_id)
        .where(interactions.c.source_corrected.is_(False), citations.c.chunk_id.is_not(None))
    )
    with registry.engine.connect() as conn:
        cited = conn.execute(query).all()

    active = index.active_chunks(serving)
    stale_ids = {chunk_id for _, chunk_id in cited if chunk_id not in active}
    doc_of = {
        stored.chunk.chunk_id: stored.chunk.doc_version for stored in index.get_chunks(stale_ids)
    }
    replaced = registry.superseded_by(set(doc_of.values()))
    retracted = registry.retracted(set(doc_of.values()))

    flags = [
        CorrectionFlag(
            request_id=request_id,
            chunk_id=chunk_id,
            doc_version=doc_of[chunk_id],
            superseded_by=replaced.get(doc_of[chunk_id]),
        )
        for request_id, chunk_id in cited
        if chunk_id in doc_of and (doc_of[chunk_id] in replaced or doc_of[chunk_id] in retracted)
    ]
    if flags:
        flagged = {flag.request_id for flag in flags}
        with registry.engine.begin() as conn:
            conn.execute(
                update(interactions)
                .where(interactions.c.request_id.in_(flagged))
                .values(source_corrected=True)
            )
    return flags
