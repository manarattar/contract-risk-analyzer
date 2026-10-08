"""Groundedness judge using the same client and retry path as analysis."""

import json

from app.config import get_settings
from app.services.risk_analyzer import _call_llm, _extract_json, _get_client


def judge_groundedness(sources, answer):
    prompt = ("Determine whether every factual claim in the answer is supported by the sources. "
              "Return only JSON: {\"grounded\": true or false, \"reason\": \"brief explanation\"}.\n\n"
              f"Sources:\n{json.dumps(sources)}\n\nAnswer:\n{answer}")
    result = _extract_json(_call_llm(_get_client(), get_settings(), prompt, temperature=0))
    if not isinstance(result, dict) or not isinstance(result.get("grounded"), bool) or not isinstance(result.get("reason"), str):
        raise ValueError("Invalid groundedness judge response")
    return result


def groundedness_rate(judgments):
    return sum(item["grounded"] for item in judgments) / len(judgments) if judgments else 1.0
