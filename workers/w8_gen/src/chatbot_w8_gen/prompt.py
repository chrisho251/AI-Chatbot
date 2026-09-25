"""The grounded prompt. Stub owned by Lane C.

Purpose
Keep the model inside the retrieved sources. Sources sit in their own data message, never mixed
with instructions, so injected text in a source cannot act as an instruction.

What to build
A Jinja2 template per prompt version. Number the contexts so the model cites them as [1], [2] and
so on. External contexts are listed after corpus contexts under an unvetted external source label.
Tell the model to answer in the style of a tutor for Health Science students and to say when the
sources are not enough. Bump PROMPT_VERSION on any change, every answer logs it.

How to test
Snapshot the rendered messages for samples.sample_generation_request.
"""

from chatbot_common.llm import Message
from chatbot_contracts.query import GenerationRequest

PROMPT_VERSION = "answer-v1"


def build_messages(request: GenerationRequest) -> list[Message]:
    raise NotImplementedError("the prompt is not written yet")
