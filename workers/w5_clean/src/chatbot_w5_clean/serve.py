"""Entrypoint of W5 clean. Routes come from chatbot_contracts.routes.

HANDLERS is what the api service calls in process. app serves the same handlers over HTTP, for
tests and for running W5 clean in its own container.
"""

from chatbot_common.http import LocalHandler
from chatbot_common.service import add_contract_routes, create_app
from chatbot_contracts.routes import CLEAN, Endpoint
from chatbot_w5_clean.online import clean_text

HANDLERS: dict[Endpoint, LocalHandler] = {CLEAN: clean_text}

app = create_app("w5_clean")
add_contract_routes(app, HANDLERS)
