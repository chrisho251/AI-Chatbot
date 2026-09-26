"""Named statistical operations. Stub owned by Lane D.

Purpose
Statistics questions need more than arithmetic. Each operation takes named variables and returns
one number, computed with SciPy or statsmodels.

What to build
Start with mean, variance, standard_deviation, confidence_interval_mean, t_test_one_sample,
t_test_two_sample, chi_square, correlation and linear_regression_slope. Document the variable
names each one expects, W8 prompts show them to the model.

How to test
Compare each operation with a worked example from the course textbook.
"""

from collections.abc import Callable

Operation = Callable[[dict[str, float]], float]

OPERATIONS: dict[str, Operation] = {}
