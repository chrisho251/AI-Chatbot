"""Prompt injection and misuse guard on the question. Stub owned by Lane C.

Purpose
Appendix B.2 asks to detect attacks, misuse and attempts to trick the model. Every detection is an
ops.guard_events row that the auditor role can review without seeing the student identity.
Also count it in GUARD_EVENTS from chatbot_common.metrics with stage gateway.
The ask flow runs the guard next to input preparation and retrieval, so its time does not add to
the latency, and holds the answer until the verdict is known.

What to build
The prompt injection classifier runs in process on CPU, inside asyncio.to_thread so the api
process never blocks. The misuse and safety guard runs on the model server, with the smallest
variant that meets the targets, see TECH_STACK.md for both. Return the worst verdict with its
category and score.

How to test
A plain statistics question is safe, a known jailbreak phrase is not. Fake the model server.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GuardVerdict:
    safe: bool
    category: str | None = None
    score: float = 0.0


async def check(text: str) -> GuardVerdict:
    raise NotImplementedError("the guard is not written yet")
