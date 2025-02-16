from datadog import initialize, statsd
import time
import random

options = {
    "statsd_host": "127.0.0.1",
    "statsd_port": 8126,
}

initialize(**options)


def log_datadog_metrics(metrics_name, value):
    statsd.gauge(metrics_name, value)


def log_datadog_event(error):
    statsd.event("ASFD system error", str(error), alert_type="error")
