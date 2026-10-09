"""Optional OpenTelemetry setup and compact application instrumentation."""

import os
import time
from contextlib import contextmanager

from opentelemetry import metrics, trace
from opentelemetry.trace import Status, StatusCode

SERVICE_NAME = "contract-analyzer-backend"
tracer = trace.get_tracer(SERVICE_NAME)
meter = metrics.get_meter(SERVICE_NAME)

llm_latency = meter.create_histogram("llm.latency_ms", unit="ms")
llm_tokens = meter.create_counter("llm.tokens", unit="tokens")
llm_retries = meter.create_counter("llm.retries", unit="1")
llm_cost = meter.create_counter("llm.cost_eur", unit="EUR")


def setup_telemetry(app):
    """Enable Azure export only when Application Insights is configured."""
    if not os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        return
    os.environ.setdefault("OTEL_SERVICE_NAME", SERVICE_NAME)
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    configure_azure_monitor()
    FastAPIInstrumentor.instrument_app(app, excluded_urls=r".*/api/health(?:\?.*)?$")


@contextmanager
def span(name: str, **attributes):
    """Record exceptions, including those later handled by pipeline fallbacks."""
    with tracer.start_as_current_span(name) as current:
        for key, value in attributes.items():
            if value is not None:
                current.set_attribute(key, value)
        try:
            yield current
        except Exception as exc:
            current.record_exception(exc)
            current.set_status(Status(StatusCode.ERROR))
            raise


def record_llm_usage(current, response, model: str, stage: str, latency_ms: float,
                     input_price: float, output_price: float):
    """Record provider reported tokens and estimated EUR cost."""
    labels = {"model": model, "stage": stage}
    current.set_attribute("llm.latency_ms", latency_ms)
    llm_latency.record(latency_ms, labels)
    usage = getattr(response, "usage", None)
    if usage is None:
        return
    input_tokens = getattr(usage, "prompt_tokens", None)
    output_tokens = getattr(usage, "completion_tokens", None)
    if input_tokens is None:
        input_tokens = getattr(usage, "input_tokens", None)
    if output_tokens is None:
        output_tokens = getattr(usage, "output_tokens", None)
    input_tokens = input_tokens if isinstance(input_tokens, (int, float)) else None
    output_tokens = output_tokens if isinstance(output_tokens, (int, float)) else None
    cost = 0.0
    for direction, count, price in (("input", input_tokens, input_price),
                                    ("output", output_tokens, output_price)):
        if count is not None:
            current.set_attribute(f"gen_ai.usage.{direction}_tokens", count)
            llm_tokens.add(count, {**labels, "direction": direction})
            cost += count * price / 1_000_000
    if input_tokens is not None or output_tokens is not None:
        current.set_attribute("llm.cost_eur", cost)
        llm_cost.add(cost, labels)


def elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000
