"""Compute or verify a value for W8. Stub owned by Lane D.

Purpose
Appendix A.4 asks W4 to perform and verify statistical and mathematical computations.

What to build
When request.operation names an entry of catalogue.OPERATIONS, compute it from request.variables.
Otherwise evaluate request.expression with SymPy using only numbers, the variables and a fixed set
of functions, never eval. Return the value, whether it is valid and a one line explanation a
student can follow. Unknown operations and bad expressions give valid false, not an exception.

How to test
sample_calc_check gives 9, an expression that calls a Python builtin is rejected.
"""

from chatbot_contracts.tools import CalcCheck, CalcResult


def check(request: CalcCheck) -> CalcResult:
    raise NotImplementedError("calculation checks are not written yet")
