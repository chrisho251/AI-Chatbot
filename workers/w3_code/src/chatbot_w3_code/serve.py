"""Entrypoint of W3 code. Routes come from chatbot_contracts.routes.

HANDLERS is what the api service calls in process. app serves the same handlers over HTTP, for
tests and for running W3 code in its own container.
"""

from chatbot_common.http import LocalHandler
from chatbot_common.service import add_contract_routes, create_app
from chatbot_contracts.routes import CODE, Endpoint
from chatbot_w3_code.solve import solve

HANDLERS: dict[Endpoint, LocalHandler] = {CODE: solve}

app = create_app("w3_code")
add_contract_routes(app, HANDLERS)
