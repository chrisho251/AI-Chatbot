"""HTTP entrypoint of W4 math. The route comes from chatbot_contracts.routes."""

from chatbot_common.service import create_app
from chatbot_contracts.routes import CALC
from chatbot_contracts.tools import CalcCheck, CalcResult
from chatbot_w4_math.calc import check

app = create_app("w4_math")


@app.post(CALC.path, response_model=CalcResult)
async def calc(request: CalcCheck) -> CalcResult:
    return check(request)
