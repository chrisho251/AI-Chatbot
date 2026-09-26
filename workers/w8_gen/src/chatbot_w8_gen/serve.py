"""Entrypoint of W8 gen. Routes come from chatbot_contracts.routes.

HANDLERS is what the api service calls in process. app serves the same handlers over HTTP, for
tests and for running W8 gen in its own container.
"""

from chatbot_common.http import LocalHandler
from chatbot_common.service import add_contract_routes, create_app
from chatbot_contracts.routes import GENERATE, GENERATE_STREAM, Endpoint
from chatbot_w8_gen.generate import generate, generate_stream

HANDLERS: dict[Endpoint, LocalHandler] = {GENERATE: generate, GENERATE_STREAM: generate_stream}

app = create_app("w8_gen")
add_contract_routes(app, HANDLERS)
