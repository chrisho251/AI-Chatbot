"""Run code in the sandbox container. Stub owned by Lane D.

Purpose
Generated code is untrusted. It only runs in the sandbox container, which has no network, no root,
a read only filesystem and CPU, memory and time limits. Only the api service, which runs W3,
can reach it, see compose.yaml.
Excel formulas run in process with excel.evaluate because they cannot touch the system.

What to build
SandboxRunner posts language, code and optional data to the sandbox at CHATBOT_SANDBOX_URL and
returns RunOutput. On AWS the same protocol talks to an ECS task with no egress.

How to test
Fake the sandbox with an httpx MockTransport. The sandbox itself has its own tests in sandbox.
"""

from dataclasses import dataclass, field
from typing import Protocol

from chatbot_contracts.enums import CodeLanguage


@dataclass(frozen=True)
class RunOutput:
    stdout: str
    duration_ms: float
    values: dict[str, float | str] = field(default_factory=dict)
    error: str | None = None


class CodeRunner(Protocol):
    async def run(self, language: CodeLanguage, code: str, data: bytes | None) -> RunOutput: ...


class SandboxRunner:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    async def run(self, language: CodeLanguage, code: str, data: bytes | None) -> RunOutput:
        raise NotImplementedError("the sandbox client is not written yet")
