"""Write code for an exercise with the LLM. Stub owned by Lane D.

What to build
One prompt per language. R and Python print the named results as JSON on the last line so the runner
can read them. For Excel the model writes cell formulas, for example T.TEST or CONFIDENCE.T, and the
data layout they refer to. Keep prompts versioned in this module.

How to test
Fake the ChatClient and assert the prompt names the language and the output format.
"""

from chatbot_common.llm import ChatClient
from chatbot_contracts.tools import CodeTask


async def write_code(task: CodeTask, llm: ChatClient) -> str:
    raise NotImplementedError("code generation is not written yet")
