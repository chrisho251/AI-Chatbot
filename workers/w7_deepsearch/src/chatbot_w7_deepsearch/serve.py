"""HTTP entrypoint of W7 deepsearch. Routes come from chatbot_contracts.routes."""

from chatbot_common.service import create_app
from chatbot_contracts.external import ExternalSearchRequest, ExternalSearchResult
from chatbot_contracts.query import RetrievalRequest, RetrievalResult
from chatbot_contracts.routes import EXTERNAL_SEARCH, RETRIEVE
from chatbot_w7_deepsearch.external import search_external
from chatbot_w7_deepsearch.internal import retrieve

app = create_app("w7_deepsearch")


@app.post(RETRIEVE.path, response_model=RetrievalResult)
async def retrieve_route(request: RetrievalRequest) -> RetrievalResult:
    return await retrieve(request)


@app.post(EXTERNAL_SEARCH.path, response_model=ExternalSearchResult)
async def external_route(request: ExternalSearchRequest) -> ExternalSearchResult:
    return await search_external(request)
