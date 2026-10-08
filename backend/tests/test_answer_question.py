from unittest.mock import Mock

import pytest

from app.config import Settings
from app.services import risk_analyzer


@pytest.mark.parametrize(
    ("response_text", "expected"),
    [
        ('{"answer": "The notice period is 30 days."}', "The notice period is 30 days."),
        ("The notice period is 30 days.", "The notice period is 30 days."),
    ],
)
def test_answer_question_uses_prose_system_message_and_unwraps_json(
    monkeypatch, response_text, expected,
):
    client = Mock()
    client.chat.completions.create.return_value.choices = [
        Mock(message=Mock(content=response_text))
    ]
    monkeypatch.setattr(risk_analyzer, "_get_client", lambda: client)
    monkeypatch.setattr(
        risk_analyzer, "get_settings", lambda: Settings(_env_file=None)
    )

    assert risk_analyzer.answer_question("What is the notice period?", ["30 days"]) == expected
    messages = client.chat.completions.create.call_args.kwargs["messages"]
    assert messages[0]["content"] == risk_analyzer.QA_SYSTEM_MESSAGE
    assert "30 days" in messages[1]["content"]
