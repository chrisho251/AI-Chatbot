"""Compare a computed result with the expected answer. Stub owned by Lane D.

What to build
Parse numbers from the expected text and from the run values, compare with a relative tolerance of
about one percent and rounding to the decimals the expected text shows. Return pass, fail or error.

How to test
Table driven cases, 9 against 9.0 passes, 0.049 against 0.05 with two decimals passes, text that
has no number gives error.
"""

from chatbot_contracts.enums import Verdict
from chatbot_w3_code.runner import RunOutput


def compare(output: RunOutput, expected: str | None) -> Verdict:
    raise NotImplementedError("result checking is not written yet")
