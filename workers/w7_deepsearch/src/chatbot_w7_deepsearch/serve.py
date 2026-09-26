"""Entrypoint of W7 deepsearch. Routes come from chatbot_contracts.routes.

HANDLERS is what the api service calls in process. app serves the same handlers over HTTP, for
tests and for running W7 deepsearch in its own container.
"""

from chatbot_common.http import LocalHandler
from chatbot_common.service import add_contract_routes, create_app
from chatbot_contracts.routes import EXTERNAL_SEARCH, RETRIEVE, Endpoint
from chatbot_w7_deepsearch.external import search_external
from chatbot_w7_deepsearch.internal import retrieve

HANDLERS: dict[Endpoint, LocalHandler] = {RETRIEVE: retrieve, EXTERNAL_SEARCH: search_external}

app = create_app("w7_deepsearch")
add_contract_routes(app, HANDLERS)
