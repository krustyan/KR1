from prometheus_client import Counter, Histogram

REQUEST_LATENCY = Histogram(
    "ppto_request_duration_seconds", "HTTP request latency", ["method", "endpoint"]
)
REQUEST_ERRORS = Counter(
    "ppto_request_errors_total", "Total HTTP request errors", ["method", "endpoint", "status"]
)
