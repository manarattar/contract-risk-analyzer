"""Offline checks for optional telemetry and provider usage capture."""
from types import SimpleNamespace

from fastapi.testclient import TestClient
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.config import Settings
from app.services.risk_analyzer import _call_llm


def test_no_connection_string_keeps_health_available(monkeypatch):
    monkeypatch.delenv("APPLICATIONINSIGHTS_CONNECTION_STRING", raising=False)
    from app.main import app
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_span_records_provider_usage(monkeypatch):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr("app.telemetry.tracer", provider.get_tracer("test"))
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))],
        usage=SimpleNamespace(prompt_tokens=12, completion_tokens=5),
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=lambda **kwargs: response)))
    settings = Settings(_env_file=None, model_name="gpt-5-mini")
    assert _call_llm(client, settings, "question", stage="qa") == "answer"
    attrs = exporter.get_finished_spans()[0].attributes
    assert attrs["gen_ai.usage.input_tokens"] == 12
    assert attrs["gen_ai.usage.output_tokens"] == 5
    assert attrs["stage"] == "qa"
