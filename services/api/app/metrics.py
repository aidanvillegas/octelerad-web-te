"""Prometheus metrics for the Macro Library API."""

from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "macro_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "macro_http_request_duration_seconds",
    "Latency of HTTP requests",
    ["method", "path"],
)

SNIPPET_MUTATIONS = Counter(
    "macro_snippet_mutations_total",
    "Count of snippet mutations",
    ["action"],
)
