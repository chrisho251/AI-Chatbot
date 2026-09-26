"""Offline enrichment entrypoint of W7. The pipeline lane runs it on a weekly schedule.

Purpose
For each course topic, search allowlisted sources for exercises with answer keys and queue the finds
as candidates with found_by enrichment. Nothing enters the knowledge base without SME triage.
"""

import argparse


def run(course_code: str, topics: list[str]) -> int:
    """Queue candidates for the topics of one course and return how many were queued."""
    raise NotImplementedError("enrichment is not written yet")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", required=True)
    parser.add_argument("--topic", action="append", required=True)
    args = parser.parse_args(argv)
    print(run(args.course, args.topic))


if __name__ == "__main__":
    main()
