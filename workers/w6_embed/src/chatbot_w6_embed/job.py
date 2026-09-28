"""Offline entrypoint of W6 embed. The pipeline lane runs it once per ingestion run.

Read the CleanPage rows of the run, chunk them with chunker.chunk_pages, embed the
chunks and write one ChunkSet with ingest.write_chunk_set. The pipeline hands these
chunk sets to the quality gate.
Dagster starts it in the app image with the run id and the document version.
"""

import argparse

from chatbot_contracts.knowledge_base import ChunkSet
from chatbot_platform.factory import Platform, build_platform
from chatbot_platform.ingest import read_clean_pages, write_chunk_set
from chatbot_w6_embed.chunker import CHUNKER_VERSION, chunk_pages
from chatbot_w6_embed.encoder import build_embedder


def run(platform: Platform, run_id: str, doc_version: str) -> int:
    """Write the ChunkSet of one document version and return the number of chunks."""
    pages = read_clean_pages(platform.engine, {run_id})
    pages = [p for p in pages if p.doc_version == doc_version]
    if not pages:
        return 0

    pages.sort(key=lambda p: p.page_no)

    settings = platform.settings
    embedding_model = settings.llm_model

    chunks = chunk_pages(pages, embedding_model)

    embedder = build_embedder(settings)
    texts = [c.text for c in chunks]
    embeddings = embedder.embed(texts)

    for chunk, embedding in zip(chunks, embeddings, strict=True):
        chunk.embedding = embedding

    chunk_set = ChunkSet(
        ingestion_run_id=run_id,
        doc_version=doc_version,
        embedding_model=embedding_model,
        chunker_version=CHUNKER_VERSION,
        chunks=chunks,
    )

    write_chunk_set(platform.engine, chunk_set)
    return len(chunks)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--doc-version", required=True)
    args = parser.parse_args(argv)
    print(run(build_platform(), args.run_id, args.doc_version))


if __name__ == "__main__":
    main()