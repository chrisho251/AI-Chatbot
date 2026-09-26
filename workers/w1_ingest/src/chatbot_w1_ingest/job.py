"""Offline entrypoint of W1 ingest. The pipeline lane runs it once per ingestion run.

Load the raw file of the document version from the registry and object store, run
layout analysis, set the page count with registry.set_page_count and append one
Region per region to ingest.regions with ingest.append_records from chatbot_platform.
Dagster starts it in the app image with the run id and the document version.
"""

import argparse

from chatbot_platform.factory import Platform, build_platform


def run(platform: Platform, run_id: str, doc_version: str) -> int:
    """Write the regions of one document version and return how many were written."""
    raise NotImplementedError("W1 ingest job is not written yet")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--doc-version", required=True)
    args = parser.parse_args(argv)
    print(run(build_platform(), args.run_id, args.doc_version))


if __name__ == "__main__":
    main()
