from pathlib import Path

from chatbot_contracts.routes import ALL_ENDPOINTS
from chatbot_contracts.schema_export import render_schemas

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"


def test_committed_schemas_match_the_models():
    expected = render_schemas()
    committed = {path.name: path.read_text(encoding="utf-8") for path in SCHEMA_DIR.glob("*.json")}
    assert committed == expected, "run the export schemas task and commit the result"


def test_endpoint_paths_are_unique_and_versioned():
    paths = [endpoint.path for endpoint in ALL_ENDPOINTS]
    assert len(paths) == len(set(paths))
    assert all(path.startswith("/v1/") for path in paths)
