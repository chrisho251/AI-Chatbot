"""Evaluate Excel formulas without Excel. Stub owned by Lane D.

Purpose
Students ask how to do an exercise in Excel. W3 writes the formulas, this module computes them so
the answer is checked before the student sees it.

What to build
Build a workbook with openpyxl from the task data, put the generated formulas in their cells and
compute them with the formulas library. Return the value of each named output cell.

How to test
AVERAGE and T.TEST on a small table give the same values as numpy and scipy.
"""


def evaluate(formulas: dict[str, str], data: list[list[float | str]]) -> dict[str, float | str]:
    raise NotImplementedError("Excel evaluation is not written yet")
