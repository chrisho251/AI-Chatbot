"""Entrypoint of W2 vision. Routes come from chatbot_contracts.routes.

HANDLERS is what the api service calls in process. app serves the same handlers over HTTP, for
tests and for running W2 vision in its own container.
"""

from chatbot_common.http import LocalHandler
from chatbot_common.service import add_contract_routes, create_app
from chatbot_contracts.routes import VISION, Endpoint
from chatbot_w2_vision.photo import read_photo

HANDLERS: dict[Endpoint, LocalHandler] = {VISION: read_photo}

app = create_app("w2_vision")
add_contract_routes(app, HANDLERS)
