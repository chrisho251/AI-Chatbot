"""Sensors that start jobs. Stub owned by Lane A.

What to build
new_documents watches registry.pending_doc_versions and starts ingest_document once per version.
sme_decisions watches gate reports that need an SME and starts publish_approved after approval.
external_candidates watches accepted candidates and uploads them as external_exercise documents.
Use run keys so a sensor never starts the same work twice.

How to test
Dagster build_sensor_context with make_test_platform data.
"""
