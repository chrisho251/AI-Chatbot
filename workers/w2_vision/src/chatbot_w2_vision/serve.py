"""HTTP entrypoint of W2 vision. The route comes from chatbot_contracts.routes."""

from chatbot_common.service import create_app
from chatbot_contracts.query import VisionRequest, VisionResult
from chatbot_contracts.routes import VISION
from chatbot_w2_vision.photo import read_photo

app = create_app("w2_vision")


@app.post(VISION.path, response_model=VisionResult)
async def vision(request: VisionRequest) -> VisionResult:
    return await read_photo(request)
