"""Offline entrypoint of W6 embed. The pipeline lane runs it once per ingestion run.

Read the CleanPage rows of the run, chunk them with chunker.chunk_pages, embed the
chunks and write one ChunkSet with lake.write_chunk_set. The pipeline hands these
chunk sets to the quality gate.
Dagster starts it in the w6 embed image with the run id and the document version.
"""

import argparse

from chatbot_platform.factory import Platform, build_platform


def run(platform: Platform, run_id: str, doc_version: str) -> int:
    """Write the ChunkSet of one document version and return the number of chunks."""
    raise NotImplementedError("W6 embed job is not written yet")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--doc-version", required=True)
    args = parser.parse_args(argv)
    print(run(build_platform(), args.run_id, args.doc_version))


if __name__ == "__main__":
    main()
