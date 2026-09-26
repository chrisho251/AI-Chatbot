"""Entrypoint of W6 embed. Routes come from chatbot_contracts.routes.

HANDLERS is what the api service calls in process. app serves the same handlers over HTTP, for
tests and for running W6 embed in its own container.
"""

from chatbot_common.http import LocalHandler
from chatbot_common.service import add_contract_routes, create_app
from chatbot_contracts.routes import EMBED, Endpoint
from chatbot_w6_embed.query import embed_query

HANDLERS: dict[Endpoint, LocalHandler] = {EMBED: embed_query}

app = create_app("w6_embed")
add_contract_routes(app, HANDLERS)
