"""Enforce the team comment rule on comments and docstrings.

Comments are English, short and use no dash, semicolon, colon or arrow characters.
Slash and ampersand are allowed. In SQL the double dash that starts a comment is allowed.
Pass file paths to check only those files, otherwise the whole repository is checked.
"""

import ast
import io
import re
import subprocess
import sys
import tokenize
from pathlib import Path

FORBIDDEN = re.compile("[\\-;:→–—]")
PRAGMAS = ("noqa", "type:", "pragma:", "fmt:", "###")
HASH_COMMENT_FILES = {".toml", ".yaml", ".yml", ".ini", ".cfg"}
SKIP_PARTS = {".venv", "node_modules", ".git", "docs"}


def _violations(text: str) -> list[str]:
    return sorted(set(FORBIDDEN.findall(text)))


def check_python(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    problems = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        body = token.string.lstrip("#").strip()
        if body.startswith("!") or body.startswith(PRAGMAS):
            continue
        if bad := _violations(body):
            problems.append(f"{path}:{token.start[0]} comment uses {bad}")
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        docstring = ast.get_docstring(node, clean=False)
        if docstring and (bad := _violations(docstring)):
            line = node.body[0].lineno
            problems.append(f"{path}:{line} docstring uses {bad}")
    return problems


def check_line_comments(path: Path, marker: str) -> list[str]:
    problems = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith(marker) or stripped.startswith("#!"):
            continue
        body = stripped[len(marker) :].strip()
        if body.startswith(PRAGMAS):
            continue
        if bad := _violations(body):
            problems.append(f"{path}:{number} comment uses {bad}")
    return problems


def check_file(path: Path) -> list[str]:
    if path.suffix == ".py":
        return check_python(path)
    if path.suffix == ".sql":
        return check_line_comments(path, "--")
    if path.suffix in HASH_COMMENT_FILES or path.name.endswith("Dockerfile"):
        return check_line_comments(path, "#")
    return []


def tracked_files(root: Path) -> list[Path]:
    try:
        output = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return [root / line for line in output.splitlines()]
    except (OSError, subprocess.CalledProcessError):
        return [path for path in root.rglob("*") if path.is_file()]


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parents[1]
    paths = [Path(arg) for arg in argv] or tracked_files(root)
    problems = []
    for path in paths:
        if SKIP_PARTS & set(path.parts) or not path.is_file():
            continue
        problems.extend(check_file(path))
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
