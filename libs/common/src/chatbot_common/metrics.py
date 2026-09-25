"""The metric catalogue. Services record these names and the Grafana dashboards read them.

Define a metric here before using it in code or in a dashboard. scripts/check_dashboards.py fails
when a dashboard uses a chatbot metric that this module does not define.
create_app records HTTP_DURATION for every route. The other metrics are recorded by the component
named in their help text, see docs/MONITORING.md for who records what.
"""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

_SECONDS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 15.0, 30.0, 60.0)
_HOURS = (60.0, 300.0, 900.0, 1800.0, 3600.0, 4 * 3600.0, 12 * 3600.0, 24 * 3600.0, 48 * 3600.0)

HTTP_DURATION = Histogram(
    "chatbot_http_request_duration_seconds",
    "Time until the response headers of an HTTP request, recorded by create_app",
    ["service", "route", "method", "status"],
    buckets=_SECONDS,
)
FIRST_TOKEN = Histogram(
    "chatbot_first_token_seconds",
    "Latency, t_first_token minus t0, recorded by the gateway",
    buckets=_SECONDS,
)
RESPONSE = Histogram(
    "chatbot_response_seconds",
    "End to end response time, t_last_byte minus t0, recorded by the gateway",
    buckets=_SECONDS,
)
REQUESTS = Counter(
    "chatbot_requests_total",
    "Questions by final level L1, L2, L3 or blocked, recorded by the gateway",
    ["level"],
)
OUTPUT_TOKENS = Counter(
    "chatbot_output_tokens_total",
    "Tokens generated for students, recorded by W8",
)
IN_FLIGHT = Gauge(
    "chatbot_requests_in_flight",
    "Questions being answered now, recorded by gateway admission control",
)
CONFIDENCE = Histogram(
    "chatbot_confidence",
    "Confidence score of each answer, recorded by the orchestrator",
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 1.0),
)
GUARD_EVENTS = Counter(
    "chatbot_guard_events_total",
    "Guard detections, recorded by the gateway and W5",
    ["detector", "stage", "category", "action"],
)
ESCALATIONS = Counter(
    "chatbot_escalations_total",
    "Level 3 escalations by stage, external or expert, recorded by the orchestrator",
    ["stage"],
)
EXTERNAL_RESPONSE = Histogram(
    "chatbot_external_response_seconds",
    "From escalation start to the external answer, recorded by the orchestrator",
    buckets=_SECONDS,
)
EXPERT_RESPONSE = Histogram(
    "chatbot_expert_response_seconds",
    "From ticket creation to the expert answer, recorded by the escalation service",
    buckets=_HOURS,
)
TOOL_CALLS = Counter(
    "chatbot_tool_calls_total",
    "Tool calls from W8 to W3 and W4 by verdict, recorded by W8",
    ["tool", "verdict"],
)
TOOL_CALL_DURATION = Histogram(
    "chatbot_tool_call_seconds",
    "Duration of a tool call, recorded by W8",
    ["tool"],
    buckets=_SECONDS,
)


def exposition() -> tuple[bytes, str]:
    """Current values in the Prometheus text format, with its content type."""
    return generate_latest(), CONTENT_TYPE_LATEST
