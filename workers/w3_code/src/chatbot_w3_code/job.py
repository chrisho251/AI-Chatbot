"""Offline entrypoint of W3 code. The pipeline lane runs it once per ingestion run.

Read the code regions of the run from ingest.regions, keep each listing verbatim in
a fenced block tagged with its language, and append one ExtractedRegion per listing.
Listings are never split, W6 keeps them whole.
Dagster starts it in the app image with the run id and the document version.
"""

import argparse

from chatbot_platform.factory import Platform, build_platform


def run(platform: Platform, run_id: str, doc_version: str) -> int:
    """Extract every code listing of the run and return the count."""
    raise NotImplementedError("W3 code job is not written yet")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--doc-version", required=True)
    args = parser.parse_args(argv)
    print(run(build_platform(), args.run_id, args.doc_version))


if __name__ == "__main__":
    main()
