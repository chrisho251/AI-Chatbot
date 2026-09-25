"""Offline entrypoint of W4 math. The pipeline lane runs it once per ingestion run.

Read the equation regions of the run from corpus.regions, turn each into normalized
LaTeX with latex.normalize and append one ExtractedRegion per equation.
Dagster starts it in the w4 math image with the run id and the document version.
"""

import argparse

from chatbot_platform.factory import Platform, build_platform


def run(platform: Platform, run_id: str, doc_version: str) -> int:
    """Normalize every equation of the run and return the count."""
    raise NotImplementedError("W4 math job is not written yet")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--doc-version", required=True)
    args = parser.parse_args(argv)
    print(run(build_platform(), args.run_id, args.doc_version))


if __name__ == "__main__":
    main()
