"""The api service. One FastAPI process for the whole online plane.

It mounts the public routes of the gateway and of the escalation service, and registers the
handlers of the orchestrator, the escalation service and the online workers W2 to W8 as local
handlers. Components call each other through shared_client, so those calls are plain function
calls with the same contracts. Only the W3 sandbox and the model servers run in other containers.
To move one component back behind HTTP, run its serve app in its own container from this image and
set CHATBOT_<SERVICE>_URL, for example CHATBOT_W2_VISION_URL. Its handlers are then left out here.
Dagster starts the same image with a worker job command for every offline step.
"""

import os
from collections.abc import Mapping

from chatbot_common.http import LocalHandler, register_local
from chatbot_common.service import create_app
from chatbot_contracts.routes import Endpoint
from chatbot_escalation import serve as escalation
from chatbot_gateway import serve as gateway
from chatbot_orchestrator import serve as orchestrator
from chatbot_w2_vision import serve as w2_vision
from chatbot_w3_code import serve as w3_code
from chatbot_w4_math import serve as w4_math
from chatbot_w5_clean import serve as w5_clean
from chatbot_w6_embed import serve as w6_embed
from chatbot_w7_deepsearch import serve as w7_deepsearch
from chatbot_w8_gen import serve as w8_gen

COMPONENTS = (
    orchestrator,
    escalation,
    w2_vision,
    w3_code,
    w4_math,
    w5_clean,
    w6_embed,
    w7_deepsearch,
    w8_gen,
)


def local_handlers(environ: Mapping[str, str] = os.environ) -> dict[Endpoint, LocalHandler]:
    """Every handler whose component has no CHATBOT_<SERVICE>_URL override."""
    return {
        endpoint: handler
        for component in COMPONENTS
        for endpoint, handler in component.HANDLERS.items()
        if f"CHATBOT_{endpoint.service.upper()}_URL" not in environ
    }


register_local(local_handlers())

app = create_app("api")
app.include_router(gateway.router)
app.include_router(escalation.router)
