"""HTTP entrypoint of W6 embed. The route comes from chatbot_contracts.routes."""

from chatbot_common.service import create_app
from chatbot_contracts.query import EmbedRequest, EmbedResult
from chatbot_contracts.routes import EMBED
from chatbot_w6_embed.query import embed_query

app = create_app("w6_embed")


@app.post(EMBED.path, response_model=EmbedResult)
async def embed(request: EmbedRequest) -> EmbedResult:
    return await embed_query(request)
