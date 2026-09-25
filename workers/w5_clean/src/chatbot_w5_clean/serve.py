"""HTTP entrypoint of W5 clean. The route comes from chatbot_contracts.routes."""

from chatbot_common.service import create_app
from chatbot_contracts.query import CleanRequest, CleanResult
from chatbot_contracts.routes import CLEAN
from chatbot_w5_clean.online import clean_text

app = create_app("w5_clean")


@app.post(CLEAN.path, response_model=CleanResult)
async def clean(request: CleanRequest) -> CleanResult:
    return await clean_text(request)
