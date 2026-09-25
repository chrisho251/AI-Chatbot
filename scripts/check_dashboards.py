"""Check the Grafana dashboards against the code they depend on.

Every chatbot metric in a query must be defined in chatbot_common.metrics, every reporting object in
a SQL query must be created by a platform migration, and every panel must use a provisioned data
source. With a database url as second argument the SQL of every panel also runs against Postgres,
which needs the platform environment for SQLAlchemy.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARDS = ROOT / "infra/local/grafana/dashboards"
DATASOURCES = ROOT / "infra/local/grafana/provisioning/datasources/datasources.yml"
CATALOGUE = ROOT / "libs/common/src/chatbot_common/metrics.py"
MIGRATIONS = ROOT / "libs/platform/src/chatbot_platform/migrations/versions"
SUFFIXES = ("_bucket", "_count", "_sum", "_created")


def defined_metrics() -> set[str]:
    return set(re.findall(r'"(chatbot_[a-z_]+)"', CATALOGUE.read_text(encoding="utf-8")))


def reporting_objects() -> set[str]:
    text = "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS.glob("*.py"))
    return set(re.findall(r"CREATE (?:TABLE|VIEW) reporting\.(\w+)", text))


def datasource_uids() -> set[str]:
    return set(re.findall(r"^\s+uid:\s*(\S+)", DATASOURCES.read_text(encoding="utf-8"), re.M))


def _base_name(metric: str) -> str:
    for suffix in SUFFIXES:
        if metric.endswith(suffix):
            return metric.removesuffix(suffix)
    return metric


def check_dashboard(path: Path, metrics: set[str], objects: set[str], uids: set[str]) -> list[str]:
    board = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    for panel in board.get("panels", []):
        where = f"{path.name} panel {panel.get('title')!r}"
        for target in panel.get("targets", []):
            uid = (target.get("datasource") or panel.get("datasource") or {}).get("uid")
            if uid not in uids:
                problems.append(f"{where} uses unknown data source {uid}")
            for metric in re.findall(r"chatbot_[a-z_]+", target.get("expr", "")):
                if _base_name(metric) not in metrics:
                    problems.append(f"{where} uses undefined metric {metric}")
            for name in re.findall(r"reporting\.(\w+)", target.get("rawSql", "")):
                if name not in objects:
                    problems.append(f"{where} reads missing reporting.{name}")
    return problems


def sql_queries() -> list[tuple[str, str]]:
    queries = []
    for path in sorted(DASHBOARDS.glob("*.json")):
        for panel in json.loads(path.read_text(encoding="utf-8")).get("panels", []):
            for target in panel.get("targets", []):
                if target.get("rawSql"):
                    queries.append((f"{path.name} {panel['title']}", target["rawSql"]))
    return queries


def run_queries_on(conn) -> list[str]:
    """Run every panel query with the Grafana time macro replaced by a fixed window."""
    from sqlalchemy import text

    problems = []
    for name, query in sql_queries():
        window = r"\1 > now() - interval '30 days'"
        executable = re.sub(r"\$__timeFilter\((\w+)\)", window, query)
        try:
            conn.execute(text(executable)).all()
        except Exception as error:
            problems.append(f"{name} fails on Postgres with {type(error).__name__}")
            conn.rollback()
    return problems


def run_queries(database_url: str) -> list[str]:
    from sqlalchemy import create_engine

    with create_engine(database_url).connect() as conn:
        return run_queries_on(conn)


def main(argv: list[str]) -> int:
    metrics, objects, uids = defined_metrics(), reporting_objects(), datasource_uids()
    boards = sorted(DASHBOARDS.glob("*.json"))
    problems = [
        problem for path in boards for problem in check_dashboard(path, metrics, objects, uids)
    ]
    board_uids = [json.loads(path.read_text(encoding="utf-8"))["uid"] for path in boards]
    if len(board_uids) != len(set(board_uids)):
        problems.append("two dashboards share a uid")
    if argv:
        problems.extend(run_queries(argv[0]))
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
