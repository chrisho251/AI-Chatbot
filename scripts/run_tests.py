"""Run the tests of every workspace package, or of the packages named on the command line.

Each package runs in its own environment, so a package never passes thanks to another one.
Extra pytest options go after a double dash separator, for example the integration marker.
"""

import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def packages() -> dict[str, Path]:
    root = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    found = {}
    for pattern in root["tool"]["uv"]["workspace"]["members"]:
        for folder in sorted(ROOT.glob(pattern)):
            project = tomllib.loads((folder / "pyproject.toml").read_text(encoding="utf-8"))
            found[project["project"]["name"]] = folder
    return found


def main(argv: list[str]) -> int:
    names, pytest_args = argv, []
    if "--" in argv:
        split = argv.index("--")
        names, pytest_args = argv[:split], argv[split + 1 :]
    selected = {name: path for name, path in packages().items() if not names or name in names}
    failed = []
    for name, folder in selected.items():
        tests = folder / "tests"
        if not tests.is_dir():
            continue
        print(f"\n=== {name} ===", flush=True)
        command = ["uv", "run", "--package", name, "pytest", str(tests), *pytest_args]
        if subprocess.run(command, cwd=ROOT).returncode not in (0, 5):
            failed.append(name)
    print("\nfailed packages " + (", ".join(failed) if failed else "none"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
