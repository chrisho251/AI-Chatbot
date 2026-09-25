"""Choose which packages CI must test, to save CI minutes.

Pass the base git revision of the change. A change to a shared library, the lock file, the root
configuration, the scripts, the Dockerfile or the workflow selects every package. Other files select
the package that contains them. Documentation only changes select nothing. When the base is unknown,
for example on the first push or a manual run, every package is selected.
Inside GitHub Actions the result is written to the step outputs packages and postgres.
"""

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FULL_RUN = (
    "libs/",
    "scripts/",
    ".github/",
    "infra/docker/",
    "uv.lock",
    "pyproject.toml",
    ".python-version",
)
POSTGRES_PATHS = ("libs/", "uv.lock", "scripts/", ".github/", "infra/local/grafana/")


def packages() -> dict[str, str]:
    """Package name to its folder relative to the repository root."""
    root = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    found = {}
    for pattern in root["tool"]["uv"]["workspace"]["members"]:
        for folder in sorted(ROOT.glob(pattern)):
            project = tomllib.loads((folder / "pyproject.toml").read_text(encoding="utf-8"))
            found[project["project"]["name"]] = folder.relative_to(ROOT).as_posix() + "/"
    return found


def changed_files(base: str) -> list[str] | None:
    """Files changed since base, or None when base cannot be compared."""
    if not base or set(base) == {"0"}:
        return None
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout.split() if result.returncode == 0 else None


def select(changed: list[str] | None, folders: dict[str, str]) -> tuple[list[str], bool]:
    """Packages to test and whether the Postgres job must run."""
    if changed is None or any(path.startswith(FULL_RUN) for path in changed):
        return sorted(folders), True
    chosen = {
        name
        for name, folder in folders.items()
        for path in changed
        if path.startswith(folder) and not path.endswith(".md")
    }
    postgres = any(path.startswith(POSTGRES_PATHS) for path in changed)
    return sorted(chosen), postgres


def main(argv: list[str]) -> int:
    chosen, postgres = select(changed_files(argv[0] if argv else ""), packages())
    lines = [f"packages={json.dumps(chosen)}", f"postgres={str(postgres).lower()}"]
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
