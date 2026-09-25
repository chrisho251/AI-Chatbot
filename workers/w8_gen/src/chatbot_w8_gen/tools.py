"""Tool calls from W8 to W4 math and W3 code. Stub owned by Lane C.

Purpose
The model must not do arithmetic or statistics in its head. It asks W4 to compute or verify values
and W3 to write and run R, Python or Excel code, then uses the verified results.

What to build
Detect a tool request from the model, OpenAI style tool calls when the server supports them or a
fixed tag format otherwise. Send CalcCheck to routes.CALC or CodeTask to routes.CODE with
ContractClient, return the result to the model and record a ToolCallRecord for each call.
Also record TOOL_CALLS and TOOL_CALL_DURATION from chatbot_common.metrics.

How to test
fake_client with sample_calc_result and sample_code_result, then assert the records.
"""

from chatbot_common.http import ContractClient
from chatbot_contracts.tools import CalcCheck, CalcResult, CodeResult, CodeTask


async def run(client: ContractClient, call: CalcCheck | CodeTask) -> CalcResult | CodeResult:
    raise NotImplementedError("tool calls are not written yet")
