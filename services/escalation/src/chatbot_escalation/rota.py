"""Who is on duty. Stub owned by Lane A.

Purpose
The Institution names the expert pool and their availability windows before M5. They live in
ops.expert_rota.

What to build
on_duty returns the expert whose window contains the given time, or None. Add a small admin command
to load the rota from a CSV file.

How to test
Two overlapping windows and a gap, checked at three times.
"""

from datetime import datetime


def on_duty(at: datetime) -> str | None:
    raise NotImplementedError("the rota is not written yet")
