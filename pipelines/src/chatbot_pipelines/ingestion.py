"""Ingestion and publication jobs. Stub owned by Lane A.

Purpose
Steps 2 to 6 of ARCHITECTURE.md section 4.4, from a registered file to a published knowledge base
version.

What to build
ingest_document starts an ingestion run with registry.start_run, runs W1, then W2, W3 and W4 in
parallel, then W5 and W6 with steps.run_step, and finishes the run with the image digests.
build_and_gate collects the finished runs, calls versioning.create_candidate, reads clean pages
and chunk sets with chatbot_platform.ingest, and runs gate.run_gate with default_checks plus the
checks of the eval lane. publish_approved calls versioning.publish once the report is approved.

How to test
Run the functions with make_test_platform and a fake run_step that writes sample rows.
"""


def ingest_document(doc_version: str) -> str:
    """Run W1 to W6 for one document version and return the ingestion run id."""
    raise NotImplementedError("the ingestion job is not written yet")


def build_and_gate(run_ids: list[str]) -> int:
    """Build a candidate from finished runs, gate it and return the candidate version."""
    raise NotImplementedError("the gate job is not written yet")


def publish_approved(version_id: int) -> None:
    raise NotImplementedError("the publish job is not written yet")
