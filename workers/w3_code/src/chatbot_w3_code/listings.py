"""Detect the language of a code listing found in a document. Stub owned by Lane D.

What to build
Simple rules first, R uses the arrow assignment and library calls, SPSS uses uppercase commands
ending with a period, Python uses import and def. Return r, spss, python or text.

How to test
One short listing per language.
"""


def detect_language(code: str) -> str:
    raise NotImplementedError("language detection is not written yet")
