"""Entrypoint of W4 math. Routes come from chatbot_contracts.routes.

HANDLERS is what the api service calls in process. app serves the same handlers over HTTP, for
tests and for running W4 math in its own container.
"""

import asyncio

from chatbot_common.http import LocalHandler
from chatbot_common.service import add_contract_routes, create_app
from chatbot_contracts.routes import CALC, Endpoint
from chatbot_contracts.tools import CalcCheck, CalcResult
from chatbot_w4_math.calc import check


async def calc(request: CalcCheck) -> CalcResult:
    """check is CPU bound, so it runs in a worker thread and never blocks the api process."""
    return await asyncio.to_thread(check, request)


HANDLERS: dict[Endpoint, LocalHandler] = {CALC: calc}

app = create_app("w4_math")
add_contract_routes(app, HANDLERS)
