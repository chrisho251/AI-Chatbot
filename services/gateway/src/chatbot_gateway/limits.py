"""Rate limits and admission control. Stub owned by Lane C.

Purpose
Keep the latency target for 10 concurrent users. A user above the per minute rate gets 429, and
when the number of requests in flight is at the limit the next one waits briefly or gets 503.

What to build
An in memory token bucket per pseudo user and a semaphore for requests in flight. Both limits come
from GatewaySettings. One api process is enough for the target load.
Keep IN_FLIGHT from chatbot_common.metrics equal to the number of admitted requests.

How to test
With a fake clock, the request above the rate is refused and the slot frees up after release.
"""


class Admission:
    def __init__(self, requests_per_minute: int, max_in_flight: int) -> None:
        self.requests_per_minute = requests_per_minute
        self.max_in_flight = max_in_flight

    async def admit(self, pseudo_user: str) -> None:
        raise NotImplementedError("admission control is not written yet")

    def release(self) -> None:
        raise NotImplementedError("admission control is not written yet")
