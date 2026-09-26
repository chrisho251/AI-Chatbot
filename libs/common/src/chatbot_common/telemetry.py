"""OpenTelemetry traces and logs for every service. Stub owned by Lane D, observability.

Purpose
Metrics already work through chatbot_common.metrics and Prometheus. This module adds traces and
logs, sent to the OTel Collector at CHATBOT_OTEL_ENDPOINT, so one request can be followed across
workers. Every span carries the attributes worker, role, request_id or ingestion_run_id.
The collector, Tempo and Loki run in the optional traces compose profile.

What to build
setup_telemetry creates a tracer provider with the service name, instruments FastAPI and httpx,
and returns nothing. Call it once from create_app. It does nothing when CHATBOT_OTEL_ENDPOINT is
empty, which is the default when the traces profile is not running. ContractClient calls in the
api process do not go through httpx, so wrap each local call in a span named after the worker.
Add the opentelemetry sdk, exporter and the FastAPI and httpx instrumentation packages to this
pyproject when implementing.

How to test
Use the in memory span exporter and assert that a request to health produces one server span.
"""


def setup_telemetry(service: str) -> None:
    raise NotImplementedError("telemetry is a Lane D task, see the module docstring")
