"""Tool calls W8 makes to W4 math and W3 code while it writes an answer."""

from pydantic import Field

from chatbot_contracts.base import Model, OnlineRecord
from chatbot_contracts.enums import CodeLanguage, Verdict


class CalcCheck(OnlineRecord):
    """Ask W4 to compute or verify a value.

    operation names an entry of the W4 catalogue, for example t_test or dosage.
    """

    operation: str
    expression: str | None = None
    variables: dict[str, float] = Field(default_factory=dict)
    units: str | None = None


class CalcResult(OnlineRecord):
    valid: bool
    explanation: str
    value: float | None = None


class CodeTask(OnlineRecord):
    """Ask W3 to write and run code that solves an exercise, then check the draft answer."""

    language: CodeLanguage
    task: str
    data_uri: str | None = None
    expected: str | None = None


class CodeResult(OnlineRecord):
    code: str
    stdout: str
    verdict: Verdict
    duration_ms: float = Field(ge=0.0)
    values: dict[str, float | str] = Field(default_factory=dict)


class ToolCallRecord(Model):
    """Summary of one tool call, kept with the generated answer."""

    tool: str
    operation: str
    verdict: Verdict
    duration_ms: float = Field(ge=0.0)
