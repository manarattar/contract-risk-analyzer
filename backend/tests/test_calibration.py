"""
Calibration tests for the contract risk analyzer.

Unit tests run without an API key (mock mode / pure-Python logic).
Integration tests (marked with @pytest.mark.integration) require OPENAI_API_KEY to be set
and make real LLM calls — run manually with: pytest -m integration
"""
import pytest
from app.schemas import (
    ContractAnalysis, ClauseAnalysis, ClauseCategory, MissingClauseRelevance, RiskLevel,
)
from app.services.mock_analyzer import get_mock_analysis
from app.services.risk_analyzer import (
    _extract_json, _clamp_score_to_category, _category_to_risk_level,
    _apply_contradiction_score_boost, _boost_contradiction_clauses,
    _derive_risk_level_from_score,
)
from app.schemas import ContradictionFinding

# ---------------------------------------------------------------------------
# Unit tests — no LLM calls
# ---------------------------------------------------------------------------

class TestJsonExtraction:
    def test_plain_json_object(self):
        assert _extract_json('{"a": 1}') == {"a": 1}

    def test_json_array(self):
        assert _extract_json('[{"x": 1}]') == [{"x": 1}]

    def test_strips_markdown_fence(self):
        raw = "```json\n{\"a\": 1}\n```"
        assert _extract_json(raw) == {"a": 1}

    def test_fallback_finds_embedded_json(self):
        raw = 'Here is the result: {"b": 2} and some text after.'
        assert _extract_json(raw) == {"b": 2}

    def test_fallback_finds_array(self):
        raw = 'Output: [{"x": 1}, {"x": 2}]'
        result = _extract_json(raw)
        assert isinstance(result, list)
        assert len(result) == 2


class TestScoreCalibration:
    def test_best_practice_score_clamped(self):
        assert _clamp_score_to_category(50, "Best Practice") == 20

    def test_critical_risk_score_clamped(self):
        assert _clamp_score_to_category(30, "Critical Risk") == 81

    def test_moderate_risk_score_within_bounds(self):
        assert _clamp_score_to_category(50, "Moderate Risk") == 50

    def test_category_to_risk_level_mapping(self):
        assert _category_to_risk_level("Best Practice") == RiskLevel.LOW
        assert _category_to_risk_level("Acceptable Standard") == RiskLevel.LOW
        assert _category_to_risk_level("Minor Improvement") == RiskLevel.LOW
        assert _category_to_risk_level("Moderate Risk") == RiskLevel.MEDIUM
        assert _category_to_risk_level("High Risk") == RiskLevel.HIGH
        assert _category_to_risk_level("Critical Risk") == RiskLevel.HIGH

    def test_derive_risk_level_from_score(self):
        assert _derive_risk_level_from_score(20) == RiskLevel.LOW
        assert _derive_risk_level_from_score(35) == RiskLevel.LOW
        assert _derive_risk_level_from_score(50) == RiskLevel.MEDIUM
        assert _derive_risk_level_from_score(70) == RiskLevel.MEDIUM
        assert _derive_risk_level_from_score(75) == RiskLevel.HIGH


class TestContradictionBoost:
    def _make_clause(self, title, score):
        return ClauseAnalysis(
            clause_title=title, clause_type="Other", original_text="...",
            category=ClauseCategory.HIGH_RISK, risk_level=RiskLevel.HIGH,
            risk_score=score, risk_explanation="x", suggested_revision="x",
            negotiation_advice="x",
        )

    def _make_contradiction(self, a, b, severity):
        return ContradictionFinding(
            clause_a_title=a, clause_b_title=b,
            contradiction_type="Logical Conflict", severity=severity,
            description="test", impact="test",
        )

    def test_score_boost_high(self):
        c = self._make_contradiction("A", "B", RiskLevel.HIGH)
        assert _apply_contradiction_score_boost(70, [c]) == 80

    def test_score_boost_medium(self):
        c = self._make_contradiction("A", "B", RiskLevel.MEDIUM)
        assert _apply_contradiction_score_boost(70, [c]) == 74

    def test_score_boost_capped_at_97(self):
        high = [self._make_contradiction("A", "B", RiskLevel.HIGH)] * 5
        assert _apply_contradiction_score_boost(90, high) == 97

    def test_clause_score_boosted_for_high_contradiction(self):
        clauses = [self._make_clause("A", 60), self._make_clause("B", 55)]
        contradiction = self._make_contradiction("A", "B", RiskLevel.HIGH)
        boosted = _boost_contradiction_clauses(clauses, [contradiction])
        assert boosted[0].risk_score == 70
        assert boosted[1].risk_score == 65

    def test_already_high_clause_not_boosted_past_90(self):
        clauses = [self._make_clause("A", 88)]
        contradiction = self._make_contradiction("A", None, RiskLevel.HIGH)
        boosted = _boost_contradiction_clauses(clauses, [contradiction])
        assert boosted[0].risk_score == 88  # already >= 85, untouched


class TestMockAnalyzer:
    def setup_method(self):
        self.analysis = get_mock_analysis()

    def test_returns_contract_analysis(self):
        assert isinstance(self.analysis, ContractAnalysis)

    def test_has_quality_summary(self):
        assert self.analysis.quality_summary is not None

    def test_has_structured_missing_clauses(self):
        for mc in self.analysis.missing_clauses:
            assert mc.relevance in MissingClauseRelevance
            assert mc.clause_type
            assert mc.reason

    def test_has_contradictions(self):
        assert len(self.analysis.contradictions) >= 1

    def test_clauses_have_category(self):
        for c in self.analysis.clauses:
            assert c.category in ClauseCategory

    def test_clauses_have_affected_party(self):
        from app.schemas import AffectedParty
        for c in self.analysis.clauses:
            assert c.affected_party in AffectedParty

    def test_has_separated_findings(self):
        assert isinstance(self.analysis.main_risks, list)
        assert isinstance(self.analysis.minor_improvements, list)
        assert isinstance(self.analysis.best_practice_clauses, list)

    def test_report_generates(self):
        from app.services.report_generator import generate_report
        buf = generate_report(self.analysis, "test.pdf")
        assert len(buf.read()) > 5000


# ---------------------------------------------------------------------------
# Integration tests — require live LLM API
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestBadContract:
    """
    Test 1: Bad contract
    Expected:
    - Overall risk score 85–100
    - Detects vague payment terms
    - Detects self-defeating confidentiality
    - Detects ownership contradiction (both parties own everything)
    - Detects total liability waiver
    - Missing clause relevance is context-aware
    """
    def setup_method(self):
        from tests.sample_contracts import BAD_CONTRACT
        from app.services.clause_splitter import split_into_clauses
        from app.services.risk_analyzer import analyze_contract
        clauses = split_into_clauses(BAD_CONTRACT)
        self.analysis = analyze_contract(clauses, full_text=BAD_CONTRACT)

    def test_high_overall_score(self):
        assert self.analysis.overall_risk_score >= 85, (
            f"Bad contract should score 85+, got {self.analysis.overall_risk_score}"
        )

    def test_detects_high_risk_or_critical_clauses(self):
        bad_cats = {ClauseCategory.HIGH_RISK, ClauseCategory.CRITICAL_RISK}
        bad_clauses = [c for c in self.analysis.clauses if c.category in bad_cats]
        assert len(bad_clauses) >= 3, "Should detect at least 3 high/critical risk clauses"

    def test_no_ownership_clause_as_best_practice(self):
        ip_clauses = [c for c in self.analysis.clauses if c.clause_type == "Intellectual Property"]
        for c in ip_clauses:
            assert c.category not in {ClauseCategory.BEST_PRACTICE, ClauseCategory.ACCEPTABLE_STANDARD}

    def test_detects_contradiction_or_critical_liability(self):
        has_contradiction = len(self.analysis.contradictions) > 0
        has_critical_liability = any(
            c.clause_type == "Liability" and c.category == ClauseCategory.CRITICAL_RISK
            for c in self.analysis.clauses
        )
        assert has_contradiction or has_critical_liability


@pytest.mark.integration
class TestGoodContract:
    """
    Test 2: Well-drafted software development contract
    Expected:
    - Overall risk score 20–40
    - Liability cap with carve-outs → Acceptable Standard or Best Practice
    - Milestone payment → not flagged as high risk
    - Written change process → Best Practice or Acceptable Standard
    - No false contradictions
    - Non-compete absence → Optional / Not Required
    """
    def setup_method(self):
        from tests.sample_contracts import GOOD_CONTRACT
        from app.services.clause_splitter import split_into_clauses
        from app.services.risk_analyzer import analyze_contract
        clauses = split_into_clauses(GOOD_CONTRACT)
        self.analysis = analyze_contract(clauses, full_text=GOOD_CONTRACT)

    def test_low_overall_score(self):
        assert self.analysis.overall_risk_score <= 45, (
            f"Good contract should score ≤45, got {self.analysis.overall_risk_score}"
        )

    def test_no_false_critical_clauses(self):
        critical = [c for c in self.analysis.clauses if c.category == ClauseCategory.CRITICAL_RISK]
        assert len(critical) == 0, f"Good contract should have no Critical Risk clauses: {[c.clause_title for c in critical]}"

    def test_liability_clause_not_high_risk(self):
        liability = [c for c in self.analysis.clauses if c.clause_type == "Liability"]
        for c in liability:
            assert c.category not in {ClauseCategory.HIGH_RISK, ClauseCategory.CRITICAL_RISK}, (
                f"Liability cap with carve-outs should not be High/Critical Risk, got {c.category}"
            )

    def test_no_false_contradictions(self):
        assert len(self.analysis.contradictions) == 0, (
            f"Good contract should have no contradictions: {[(c.clause_a_title, c.clause_b_title) for c in self.analysis.contradictions]}"
        )

    def test_non_compete_absence_not_essential(self):
        nc_missing = [mc for mc in self.analysis.missing_clauses if "non-compete" in mc.clause_type.lower()]
        for mc in nc_missing:
            assert mc.relevance == MissingClauseRelevance.OPTIONAL, (
                f"Non-compete should be Optional for software dev contract, got {mc.relevance}"
            )


@pytest.mark.integration
class TestIncompleteContract:
    """
    Test 3: Good structure but missing key clauses
    Expected:
    - Overall risk score 40–60
    - Standard clauses not flagged as high risk
    - Missing acceptance criteria, indemnity, data protection identified
    - Missing clauses relevance-classified appropriately
    """
    def setup_method(self):
        from tests.sample_contracts import INCOMPLETE_CONTRACT
        from app.services.clause_splitter import split_into_clauses
        from app.services.risk_analyzer import analyze_contract
        clauses = split_into_clauses(INCOMPLETE_CONTRACT)
        self.analysis = analyze_contract(clauses, full_text=INCOMPLETE_CONTRACT)

    def test_mid_range_score(self):
        score = self.analysis.overall_risk_score
        assert 30 <= score <= 65, f"Incomplete contract should score 30–65, got {score}"

    def test_no_false_critical_clauses(self):
        critical = [c for c in self.analysis.clauses if c.category == ClauseCategory.CRITICAL_RISK]
        assert len(critical) == 0, f"Incomplete but decent contract should not have Critical Risk clauses: {[c.clause_title for c in critical]}"

    def test_identifies_missing_essential_or_recommended(self):
        important = [
            mc for mc in self.analysis.missing_clauses
            if mc.relevance in {MissingClauseRelevance.ESSENTIAL, MissingClauseRelevance.RECOMMENDED}
        ]
        assert len(important) >= 1, "Should flag at least one Essential or Recommended missing clause"

    def test_non_compete_not_flagged_as_essential(self):
        nc_missing = [mc for mc in self.analysis.missing_clauses if "non-compete" in mc.clause_type.lower()]
        for mc in nc_missing:
            assert mc.relevance != MissingClauseRelevance.ESSENTIAL
