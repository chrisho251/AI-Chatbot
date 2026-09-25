"""Offline entrypoint of W2 vision. The pipeline lane runs it once per ingestion run.

Read the regions W2 handles for the run from corpus.regions, see REGION_HANDLERS.
Run OCR on scans and image tables, caption figures, and append one ExtractedRegion
per region to corpus.extracted_regions.
Dagster starts it in the w2 vision image with the run id and the document version.
"""

import argparse

from chatbot_platform.factory import Platform, build_platform


def run(platform: Platform, run_id: str, doc_version: str) -> int:
    """Extract every figure, scan and table region of the run and return the count."""
    raise NotImplementedError("W2 vision job is not written yet")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--doc-version", required=True)
    args = parser.parse_args(argv)
    print(run(build_platform(), args.run_id, args.doc_version))


if __name__ == "__main__":
    main()
