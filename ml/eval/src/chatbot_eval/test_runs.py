"""Internal testing levels of Appendix C. Stub owned by Lane D.

Purpose
For each test cycle record the questions per level, the system responses, RAGAs scores where they
apply, the level 3 escalations and the remediation. This is the M6 deliverable.

What to build
Send every test case to the gateway ask endpoint with a test student token, collect the events,
and write eval.test_runs. Level 3 passes when the stream carries a status.external_search or a
status.expert_pending event.

How to test
Fake the gateway stream with sample events for one case per level.
"""


def run_cycle(cycle_id: str) -> int:
    """Run every test case once and return how many were recorded."""
    raise NotImplementedError("test cycles are not written yet")
