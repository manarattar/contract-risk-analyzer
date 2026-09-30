"""
Unit tests for the Jev clause judge — no network calls.

Jev's HTTP responses are faked, so these check the parts that are our code:
the score formula, how answers are mapped onto ClauseAnalysis, and the
fallback to the LLM when Jev can't be reached.
"""
import pytest
from app.schemas import ClauseCategory, RiskLevel
from app.services import jev_judge, risk_analyzer


def _jev_response(
    category_probs, clause_type="Liability", party="Client", enforceable_p=0.1
):
    top = max(category_probs, key=category_probs.get)
    return {
        "model": "jev-1.13.0",
        "answers": {
            "category": {
                "type": "choice",
                "choice": top,
                "confidence": 0.9,
                "probabilities": category_probs,
            },
            "clause_type": {
                "type": "choice",
                "choice": clause_type,
                "confidence": 0.9,
                "probabilities": {clause_type: 1.0},
            },
            "affected_party": {
                "type": "choice",
                "choice": party,
                "confidence": 0.9,
                "probabilities": {party: 1.0},
            },
            "enforceability_concern": {"type": "noul", "noul": enforceable_p},
        },
    }


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture
def fake_jev(monkeypatch):
    """Answer each clause with the probabilities registered for its text."""
    answers = {}

    def fake_post(self, url, headers=None, json=None):
        return _FakeResponse(answers[json["state"]["clause"]])

    monkeypatch.setattr(jev_judge.httpx.Client, "post", fake_post)
    return answers


class TestRiskScoreFormula:
    def test_certain_category_gives_its_midpoint(self):
        assert jev_judge.risk_score_from_probabilities({"High Risk": 1.0}) == 70

    def test_split_lands_between_categories(self):
        score = jev_judge.risk_score_from_probabilities(
            {"Moderate Risk": 0.5, "High Risk": 0.5}
        )
        assert score == 60

    def test_unnormalised_probabilities_are_normalised(self):
        score = jev_judge.risk_score_from_probabilities(
            {"Best Practice": 0.2, "Critical Risk": 0.2}
        )
        assert score == 50


class TestJudgeClauses:
    def test_decisions_keep_clause_order(self, fake_jev):
        fake_jev["a"] = _jev_response({"Best Practice": 0.9, "High Risk": 0.1})
        fake_jev["b"] = _jev_response({"Critical Risk": 0.95, "High Risk": 0.05})
        decisions = jev_judge.judge_clauses(
            [{"text": "a"}, {"text": "b"}], "NDA", "Client"
        )
        assert [d["category"] for d in decisions] == ["Best Practice", "Critical Risk"]

    def test_low_confidence_is_flagged_for_review(self, fake_jev):
        payload = _jev_response(
            {"Moderate Risk": 0.4, "High Risk": 0.35, "Acceptable Standard": 0.25}
        )
        payload["answers"]["category"]["confidence"] = 0.2
        fake_jev["a"] = payload
        decision = jev_judge.judge_clauses([{"text": "a"}], "NDA", "Client")[0]
        assert decision["needs_review"] is True

    def test_enforceability_uses_half_as_threshold(self, fake_jev):
        fake_jev["a"] = _jev_response({"Critical Risk": 1.0}, enforceable_p=0.7)
        fake_jev["b"] = _jev_response({"Best Practice": 1.0}, enforceable_p=0.3)
        a, b = jev_judge.judge_clauses([{"text": "a"}, {"text": "b"}], "NDA", "Client")
        assert a["enforceability_concern"] is True
        assert b["enforceability_concern"] is False


class TestBatchWithJev:
    def test_jev_decides_and_llm_only_writes_text(self, fake_jev, monkeypatch):
        fake_jev["We accept no liability of any kind."] = _jev_response(
            {"Critical Risk": 0.8, "High Risk": 0.2},
            clause_type="Liability",
            party="Client",
            enforceable_p=0.9,
        )
        llm_text = (
            '[{"clause_title":"Total liability waiver","what_works_well":"None",'
            '"risk_explanation":"Removes all remedies.","suggested_revision":"Cap it.",'
            '"negotiation_advice":"Reject."}]'
        )
        monkeypatch.setattr(risk_analyzer, "_call_llm", lambda *a, **k: llm_text)
        monkeypatch.setattr(risk_analyzer, "_get_client", lambda: None)

        [clause] = risk_analyzer._analyze_clauses_batch_with_jev(
            [{"index": 0, "text": "We accept no liability of any kind."}],
            "Service Agreement",
            "Client",
        )
        assert clause.decided_by == "jev"
        assert clause.category == ClauseCategory.CRITICAL_RISK
        assert clause.risk_level == RiskLevel.HIGH
        # 0.8 * 90 + 0.2 * 70 = 86, inside the Critical Risk band
        assert clause.risk_score == 86
        assert clause.enforceability_concern is True
        assert clause.clause_title == "Total liability waiver"

    def test_missing_llm_text_keeps_jev_decision(self, fake_jev, monkeypatch):
        fake_jev["x"] = _jev_response({"Best Practice": 1.0})
        monkeypatch.setattr(risk_analyzer, "_call_llm", lambda *a, **k: "not json")
        monkeypatch.setattr(risk_analyzer, "_get_client", lambda: None)
        monkeypatch.setattr(risk_analyzer.time, "sleep", lambda s: None)

        [clause] = risk_analyzer._analyze_clauses_batch_with_jev(
            [{"index": 0, "text": "x"}], "NDA", "Both Equal"
        )
        assert clause.category == ClauseCategory.BEST_PRACTICE
        assert clause.clause_title == "Clause 1"

    def test_falls_back_to_llm_when_jev_fails(self, monkeypatch):
        monkeypatch.setattr(risk_analyzer, "jev_available", lambda: True)

        def jev_down(*args, **kwargs):
            raise ConnectionError("jev unreachable")

        monkeypatch.setattr(risk_analyzer, "_analyze_clauses_batch_with_jev", jev_down)
        llm_json = (
            '[{"clause_title":"Payment","clause_type":"Payment","category":"Acceptable Standard",'
            '"risk_score":15,"affected_party":"Both Parties","what_works_well":"Clear.",'
            '"risk_explanation":"None","suggested_revision":"None required",'
            '"negotiation_advice":"None required","enforceability_concern":false}]'
        )
        monkeypatch.setattr(risk_analyzer, "_call_llm", lambda *a, **k: llm_json)
        monkeypatch.setattr(risk_analyzer, "_get_client", lambda: None)

        [clause] = risk_analyzer._analyze_clauses_batch(
            [{"index": 0, "text": "Pay in 30 days."}], "NDA", "Client"
        )
        assert clause.decided_by == "llm"
        assert clause.category == ClauseCategory.ACCEPTABLE_STANDARD
