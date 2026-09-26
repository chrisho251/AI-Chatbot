"""Entrypoint of the orchestrator. The gateway is its only caller.

HANDLERS is what the api service calls in process. app serves the same handlers over HTTP, for
tests and for running the orchestrator in its own container.
"""

from chatbot_common.http import LocalHandler
from chatbot_common.service import add_contract_routes, create_app
from chatbot_contracts.routes import ANSWER, Endpoint
from chatbot_orchestrator.pipeline import answer

HANDLERS: dict[Endpoint, LocalHandler] = {ANSWER: answer}

app = create_app("orchestrator")
add_contract_routes(app, HANDLERS)
