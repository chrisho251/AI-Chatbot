"""Offline entrypoint of W5 clean. The pipeline lane runs it once per ingestion run.

Join the text regions and the ExtractedRegion rows of every page in reading order,
normalize, strip boilerplate, scrub PII, scan for injected instructions and mark
duplicates. Append exactly one CleanPage per page to ingest.cleaned_pages, blank
pages included, with PageFlags filled in for the quality gate.
Dagster starts it in the app image with the run id and the document version.
"""

import argparse

from chatbot_platform.factory import Platform, build_platform


def run(platform: Platform, run_id: str, doc_version: str) -> int:
    """Write one CleanPage per page of the document version and return the count."""
    raise NotImplementedError("W5 clean job is not written yet")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--doc-version", required=True)
    args = parser.parse_args(argv)
    print(run(build_platform(), args.run_id, args.doc_version))


if __name__ == "__main__":
    main()
