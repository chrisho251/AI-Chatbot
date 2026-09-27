"""Text normalization and boilerplate removal.

Purpose
Fix encoding damage, unify whitespace and quotes, and remove running headers, footers and page
numbers that repeat on most pages of a document.

What to build
normalize fixes one text with ftfy and whitespace rules.
strip_boilerplate receives the pages of one document and drops lines that repeat on more than half
of the pages. Keep equations, code fences and tables untouched.

How to test
Three pages that share a header and a footer come back without them and nothing else changes.
"""

import re
from collections import defaultdict

import ftfy

_CODE_FENCE = "```"
_DISPLAY_MATH = "$$"


def normalize(text: str) -> str:
    """Fix encoding damage, unify whitespace and quotes."""
    text = ftfy.fix_text(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _count_lines(pages: list[str]) -> dict[str, int]:
    """Count how many pages each non-blank line appears on."""
    counts: dict[str, int] = defaultdict(int)
    for page in pages:
        seen: set[str] = set()
        for line in page.splitlines():
            if line.strip():
                seen.add(line)
        for line in seen:
            counts[line] += 1
    return counts


def strip_boilerplate(pages: list[str]) -> list[str]:
    """Drop lines that repeat on more than half of the pages."""
    if len(pages) <= 1:
        return list(pages)
    threshold = len(pages) // 2 + 1
    counts = _count_lines(pages)
    boilerplate = {line for line, count in counts.items() if count >= threshold}
    return [_strip_page(page, boilerplate) for page in pages]


def _strip_page(page: str, boilerplate: set[str]) -> str:
    """Remove boilerplate lines from one page, keeping code tables and equations."""
    in_code = False
    in_math = False
    cleaned: list[str] = []
    for line in page.splitlines():
        stripped = line.strip()
        if stripped.startswith(_CODE_FENCE):
            in_code = not in_code
            cleaned.append(line)
        elif in_code:
            cleaned.append(line)
        elif stripped.startswith(_DISPLAY_MATH):
            in_math = not in_math
            cleaned.append(line)
        elif in_math or stripped.startswith("|") or "$" in line:
            cleaned.append(line)
        elif stripped and line in boilerplate:
            continue
        else:
            cleaned.append(line)
    return "\n".join(cleaned)
