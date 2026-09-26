import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_comment_rule_flags_forbidden_characters(tmp_path):
    check = _load("check_comments")
    bad = tmp_path / "bad.py"
    bad.write_text('"""Read-only store."""\n\nx = 1  # one; two\n', encoding="utf-8")
    good = tmp_path / "good.py"
    good.write_text(
        '"""Read only store, see a/b & c."""\n\nx = 1  # noqa: E501\n', encoding="utf-8"
    )
    sql = tmp_path / "init.sql"
    sql.write_text("-- create the test database\n-- bad: colon\n", encoding="utf-8")
    assert len(check.check_file(bad)) == 2
    assert check.check_file(good) == []
    assert len(check.check_file(sql)) == 1


def test_the_repository_follows_the_comment_rule():
    assert _load("check_comments").main([]) == 0


def test_lanes_only_share_libraries():
    boundaries = _load("check_boundaries")
    assert boundaries.violations(boundaries.members()) == []
    graph = {"chatbot-w8-gen": {"chatbot-w4-math"}, "chatbot-platform": {"chatbot-common"}}
    assert len(boundaries.violations(graph)) == 2
    composed = {
        "chatbot-api": {"chatbot-w8-gen", "chatbot-gateway"},
        "chatbot-w8-gen": {"chatbot-api"},
        "chatbot-gateway": set(),
        "chatbot-pipelines": set(),
    }
    assert boundaries.violations(composed) == ["chatbot-w8-gen must not depend on chatbot-api"]
    assert boundaries.violations({"chatbot-api": {"chatbot-pipelines"}, "chatbot-pipelines": set()})


def test_dashboards_match_metrics_views_and_data_sources():
    dashboards = _load("check_dashboards")
    assert dashboards.main([]) == 0


def test_dashboard_check_flags_unknown_names(tmp_path):
    dashboards = _load("check_dashboards")
    board = tmp_path / "bad.json"
    board.write_text(
        '{"uid": "x", "panels": [{"title": "p", "targets": ['
        '{"datasource": {"uid": "prometheus"}, "expr": "rate(chatbot_made_up_total[5m])"},'
        '{"datasource": {"uid": "platform"}, "rawSql": "SELECT * FROM reporting.nothing"},'
        '{"datasource": {"uid": "elsewhere"}, "expr": "up"}]}]}',
        encoding="utf-8",
    )
    problems = dashboards.check_dashboard(
        board,
        dashboards.defined_metrics(),
        dashboards.reporting_objects(),
        dashboards.datasource_uids(),
    )
    assert len(problems) == 3


def test_ci_selects_only_touched_packages():
    changed = _load("changed_packages")
    folders = {"chatbot-w6-embed": "workers/w6_embed/", "chatbot-w8-gen": "workers/w8_gen/"}
    assert changed.select(["workers/w6_embed/src/x.py"], folders) == (["chatbot-w6-embed"], False)
    assert changed.select(["workers/w8_gen/README.md", "docs/TECH_STACK.md"], folders) == (
        [],
        False,
    )
    assert changed.select(["libs/platform/src/x.py"], folders)[0] == sorted(folders)
    assert changed.select(None, folders) == (sorted(folders), True)
    assert set(changed.packages()) >= {"chatbot-platform", "chatbot-w6-embed"}
