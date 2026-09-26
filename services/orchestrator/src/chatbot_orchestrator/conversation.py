"""Conversation memory. Stub owned by Lane C.

Purpose
Students ask follow ups such as now do part b. Retrieval needs the full question, and W8 needs the
earlier turns to answer in context.

What to build
load_history reads the last max_turns interactions of the conversation from ops.interactions,
oldest first, checks that they belong to the same pseudo user, and decrypts the question text with
the KeyService from chatbot_common.keys. Turns whose text was blanked by retention are skipped.
standalone_question returns the question unchanged when there is no history. Otherwise it asks the
LLM once, with a short versioned prompt, to rewrite the question so it stands alone.
interactions.record upserts ops.conversations with the last active time.

How to test
Two logged turns come back in order, a turn of another pseudo user is refused, and a faked LLM
receives the history and the new question.
"""

from chatbot_common.llm import ChatClient
from chatbot_contracts.query import Turn

REWRITE_PROMPT_VERSION = "standalone-v1"


def load_history(conversation_id: str, pseudo_user: str, max_turns: int) -> list[Turn]:
    raise NotImplementedError("conversation history is not written yet")


async def standalone_question(question: str, history: list[Turn], llm: ChatClient) -> str:
    raise NotImplementedError("question rewriting is not written yet")
