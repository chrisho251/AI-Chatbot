"""Log every answered request. Stub owned by Lane C.

Purpose
Reproducible answers. Write the ops.interactions row with the conversation id, the knowledge base
version, model and prompt versions, confidence, level and flags, one ops.citations row per kept
citation and one ops.tool_calls row per tool call, and upsert the ops.conversations row. The
question is stored encrypted with the KeyService, see ARCHITECTURE.md section 8.

What to build
Insert with SQLAlchemy Core into the tables of chatbot_platform.sql through build_platform.
Keep it one transaction per request.

How to test
Use make_test_platform and assert the rows, then run chatbot_platform.lineage.sweep_superseded on
them to see the lineage sweep work with your data.
"""

from chatbot_contracts.enums import ConfidenceLevel
from chatbot_contracts.query import AskRequest, GenerationResult


def record(
    request: AskRequest,
    result: GenerationResult,
    kb_version: int,
    confidence: float,
    level: ConfidenceLevel,
    used_external: bool,
    escalated: bool,
) -> None:
    raise NotImplementedError("interaction logging is not written yet")
