"""HTTP entrypoint of W3 code. The route comes from chatbot_contracts.routes."""

from chatbot_common.service import create_app
from chatbot_contracts.routes import CODE
from chatbot_contracts.tools import CodeResult, CodeTask
from chatbot_w3_code.solve import solve

app = create_app("w3_code")


@app.post(CODE.path, response_model=CodeResult)
async def code(task: CodeTask) -> CodeResult:
    return await solve(task)
