"""Command line for operators and the pipeline lane. The help flag lists every command.

Every command reads its settings from PLATFORM_ environment variables or the .env file.
Results are printed as JSON so scripts can read them.
"""

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from chatbot_contracts.enums import SourceType
from chatbot_platform import documents, lineage, migrate, retention, versioning
from chatbot_platform.factory import Platform, build_platform
from chatbot_platform.models import CANDIDATE_ALIAS, SERVING_ALIAS
from chatbot_platform.settings import BUCKETS


def _print(value: object) -> None:
    print(json.dumps(value, indent=2, default=str))


def cmd_init(platform: Platform, _args: argparse.Namespace) -> None:
    migrate.upgrade(platform.settings.database_url, platform.settings.embedding_dim)
    for bucket in BUCKETS:
        platform.store.ensure_bucket(bucket)
    _print({"database": "migrated", "buckets": BUCKETS})


def cmd_upload(platform: Platform, args: argparse.Namespace) -> None:
    path = Path(args.file)
    document = documents.register_document(
        platform.registry,
        platform.store,
        path.read_bytes(),
        filename=path.name,
        course_code=args.course,
        source_id=args.source_id,
        source_type=SourceType(args.type),
        licence=args.licence,
        source_url=args.url,
        producer="platform_cli",
    )
    _print(document.model_dump(mode="json"))


def cmd_status(platform: Platform, _args: argparse.Namespace) -> None:
    registry = platform.registry
    _print(
        {
            "serving": registry.get_alias(SERVING_ALIAS),
            "candidate": registry.get_alias(CANDIDATE_ALIAS),
            "versions": [
                {"version": m.version_id, "status": m.status, "documents": len(m.doc_versions)}
                for m in registry.list_kb_versions()
            ],
            "pending_documents": registry.pending_doc_versions(),
        }
    )


def cmd_rollback(platform: Platform, args: argparse.Namespace) -> None:
    versioning.rollback(platform.registry, args.version)
    _print({"serving": args.version})


def cmd_trace(platform: Platform, args: argparse.Namespace) -> None:
    trace = lineage.trace_citation(platform.registry, platform.index, args.chunk_id)
    _print(trace.model_dump(mode="json"))


def cmd_sweep_lineage(platform: Platform, _args: argparse.Namespace) -> None:
    flags = lineage.sweep_superseded(platform.registry, platform.index)
    _print([flag.model_dump(mode="json") for flag in flags])


def cmd_retention(platform: Platform, _args: argparse.Namespace) -> None:
    results = retention.run_retention(platform.engine, platform.store, platform.settings)
    _print([{"target": result.target, "deleted": result.deleted} for result in results])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chatbot-platform", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("init", help="migrate the database and create the buckets")

    upload = commands.add_parser("upload", help="register a source file")
    upload.add_argument("file")
    upload.add_argument("--course", required=True)
    upload.add_argument("--source-id", required=True)
    upload.add_argument("--type", required=True, choices=[t.value for t in SourceType])
    upload.add_argument("--licence")
    upload.add_argument("--url")

    commands.add_parser("status", help="show aliases, versions and pending documents")

    rollback = commands.add_parser("rollback", help="point serving at an older published version")
    rollback.add_argument("version", type=int)

    trace = commands.add_parser("trace", help="trace a cited chunk back to its raw file")
    trace.add_argument("chunk_id")

    commands.add_parser("sweep-lineage", help="flag answers that cited corrected sources")
    commands.add_parser("retention", help="delete data older than its retention limit")
    return parser


COMMANDS: dict[str, Callable[[Platform, argparse.Namespace], None]] = {
    "init": cmd_init,
    "upload": cmd_upload,
    "status": cmd_status,
    "rollback": cmd_rollback,
    "trace": cmd_trace,
    "sweep-lineage": cmd_sweep_lineage,
    "retention": cmd_retention,
}


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    COMMANDS[args.command](build_platform(), args)


if __name__ == "__main__":
    main(sys.argv[1:])
