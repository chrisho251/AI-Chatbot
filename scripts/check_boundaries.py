"""Keep lanes independent by checking which workspace packages may depend on which.

Services, workers, pipelines and ml packages may only depend on the shared libraries.
They talk to each other through contracts, never through imports.
The api package is the one exception. It composes the services and workers into one process, so it
may depend on all of them, and no package may depend on it.
"""

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = {"chatbot-contracts", "chatbot-common", "chatbot-platform"}
COMPOSER = "chatbot-api"
NOT_COMPOSED = {"chatbot-pipelines", "chatbot-eval", "chatbot-finetune", COMPOSER}
ALLOWED = {
    "chatbot-contracts": set(),
    "chatbot-common": {"chatbot-contracts"},
    "chatbot-platform": {"chatbot-contracts"},
}


def members() -> dict[str, set[str]]:
    """Package name to the internal packages it depends on."""
    root = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    found = {}
    for pattern in root["tool"]["uv"]["workspace"]["members"]:
        for folder in sorted(ROOT.glob(pattern)):
            project = tomllib.loads((folder / "pyproject.toml").read_text(encoding="utf-8"))
            dependencies = project["project"].get("dependencies", [])
            names = {dep.split(">")[0].split("=")[0].split("[")[0].strip() for dep in dependencies}
            found[project["project"]["name"]] = {
                name for name in names if name.startswith("chatbot")
            }
    return found


def violations(graph: dict[str, set[str]]) -> list[str]:
    problems = []
    for package, internal in sorted(graph.items()):
        allowed = ALLOWED.get(package, SHARED)
        if package == COMPOSER:
            allowed = set(graph) - NOT_COMPOSED
        for dependency in sorted(internal - allowed):
            problems.append(f"{package} must not depend on {dependency}")
    return problems


def main() -> int:
    problems = violations(members())
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
