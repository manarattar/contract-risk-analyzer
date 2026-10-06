from unittest.mock import Mock

import pytest

from app.config import Settings
from app.services.risk_analyzer import _call_llm


@pytest.mark.parametrize("use_temperature", [True, False])
def test_call_llm_temperature_option(use_temperature):
    client = Mock()
    client.chat.completions.create.return_value.choices = [Mock(message=Mock(content="response"))]
    settings = Settings(_env_file=None, llm_use_temperature=use_temperature)

    assert _call_llm(client, settings, "prompt", temperature=0.3) == "response"

    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-4o-mini"
    assert kwargs["messages"][1]["content"] == "prompt"
    if use_temperature:
        assert kwargs["temperature"] == 0.3
    else:
        assert "temperature" not in kwargs
