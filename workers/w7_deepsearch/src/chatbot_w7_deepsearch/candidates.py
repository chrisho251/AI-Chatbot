"""Queue external finds for SME triage. Stub owned by Lane C.

Purpose
External finds may enrich the knowledge base, but only after an SME accepts them and they pass the
quality gate like any other document. Accepted candidates are uploaded with source type
external_exercise and their licence.

What to build
Insert an ExternalCandidate into ops.external_candidates unless the same snapshot sha256 is already
queued. Keep the snapshot in the external bucket so the SME sees exactly what the model saw.

How to test
Queue the same page twice with make_test_platform and assert one row.
"""

from chatbot_contracts.external import ExternalCandidate


def queue(candidate: ExternalCandidate) -> None:
    raise NotImplementedError("candidate queue is not written yet")
