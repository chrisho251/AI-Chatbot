"""Solve a computational exercise at answer time. Stub owned by Lane D.

Purpose
Appendix A.4 asks W3 to generate, execute and check code in Excel, R and Python exercises.

What to build
generate.write_code for the task language, runner.run in the sandbox, then check.compare against
task.expected when it is given. Return the code, stdout, named values and a verdict. Errors and
timeouts return verdict error, never an exception, so W8 can still answer without the result.

How to test
Fake the LLM and the sandbox, one test per language, one for a timeout.
"""

from chatbot_contracts.tools import CodeResult, CodeTask


async def solve(task: CodeTask) -> CodeResult:
    raise NotImplementedError("solving is not written yet")
