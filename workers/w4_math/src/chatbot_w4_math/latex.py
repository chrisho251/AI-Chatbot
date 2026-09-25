"""Normalize LaTeX from OCR and layout analysis. Stub owned by Lane D.

What to build
Clean spacing and delimiters, unify common macros and check that SymPy can parse the result when it
is an equation. Keep the original when parsing fails and lower the confidence instead.

How to test
Two spellings of the same formula normalize to the same string.
"""


def normalize(latex: str) -> tuple[str, float]:
    """The normalized LaTeX and a confidence between 0 and 1."""
    raise NotImplementedError("LaTeX normalization is not written yet")
