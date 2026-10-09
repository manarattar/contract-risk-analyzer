import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from evals.metrics import (aggregate_metrics, answer_correct, clause_metrics, match_clauses,
                           missing_counts, missing_recall, retrieval_hit, score_stability)


def clause(text, level):
    return SimpleNamespace(original_text=text, risk_level=SimpleNamespace(value=level))


def test_clause_matching_and_metrics():
    labels = [{"match": "1. Liability", "expected_risk": "High"},
              {"match": "2. Payment", "expected_risk": "Low"},
              {"match": "3. Privacy", "expected_risk": "High"}]
    matches = match_clauses([clause("1. Liability\nNo cap", "High"),
                             clause("2. Payment\n30 days", "High")], labels)
    result = clause_metrics(matches)
    assert result["matched_clauses"] == 2
    assert (result["tp"], result["fp"], result["fn"]) == (1, 1, 1)
    assert (result["exact"], result["near"], result["count"]) == (1, 1, 3)
    assert result["risky_recall"] == 0.5
    assert result["risky_precision"] == 0.5
    assert result["risky_f1"] == 0.5
    assert result["exact_level_accuracy"] == pytest.approx(1 / 3)
    assert result["within_one_level_accuracy"] == pytest.approx(1 / 3)


def test_missing_recall():
    expected = [{"name": "Disputes", "aliases": ["arbitration", "dispute resolution"]},
                {"name": "Security", "aliases": ["data protection"]}]
    actual = [SimpleNamespace(clause_type="Dispute Resolution", reason="No process")]
    assert missing_counts(expected, actual) == (1, 2)
    assert missing_counts([], actual) == (0, 0)
    assert missing_recall(expected, actual) == 0.5
    assert missing_recall([], actual) == 1


def test_aggregate_pools_counts_and_questions():
    risky = clause_metrics(match_clauses([clause("1. Liability", "Low")],
                                          [{"match": "1. Liability", "expected_risk": "High"}]))
    risky.update(missing_hits=0, missing_expected=2)
    clean = clause_metrics(match_clauses([clause("1. Payment", "Low"),
                                          clause("2. Term", "Low")],
                                         [{"match": "1. Payment", "expected_risk": "Low"},
                                          {"match": "2. Term", "expected_risk": "Low"}]))
    clean.update(missing_hits=1, missing_expected=1)
    results = [
        {"metrics": risky, "questions": [{"retrieval_hit": False, "answer_correct": False,
                                          "grounded": False}]},
        {"metrics": clean, "questions": [{"retrieval_hit": True, "answer_correct": True,
                                          "grounded": True} for _ in range(3)]},
    ]
    aggregate = aggregate_metrics(results)
    assert aggregate["risky_precision"] == 0
    assert aggregate["risky_recall"] == 0
    assert aggregate["risky_f1"] == 0
    assert aggregate["exact_level_accuracy"] == pytest.approx(2 / 3)
    assert aggregate["within_one_level_accuracy"] == pytest.approx(2 / 3)
    assert aggregate["missing_recall"] == pytest.approx(1 / 3)
    assert aggregate["retrieval_hit_rate"] == 0.75
    assert aggregate["answer_correctness"] == 0.75
    assert aggregate["groundedness"] == 0.75


def test_retrieval_and_answer():
    assert retrieval_hit("  90 days notice ", ["irrelevant", "Give  90\n days notice."], 2)
    assert not retrieval_hit("90 days notice", ["irrelevant", "90 days notice"], 1)
    assert answer_correct("Notice is ninety days and in writing", [["90 days", "ninety days"], ["writing", "written"]])
    assert not answer_correct("Notice is 90 days", [["90 days"], ["written"]])


def test_stability():
    assert score_stability([10, 20])["range"] == 10
    assert score_stability([10, 20])["stdev"] == 5
    assert score_stability([])["range"] is None


def test_golden_schema():
    files = list((Path(__file__).parents[1] / "evals" / "golden").glob("*.json"))
    assert len(files) == 6
    assert {json.loads(path.read_text(encoding="utf-8"))["id"] for path in files} == {
        "bad", "good", "incomplete", "nda", "saas", "consulting",
    }
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["id"] and data["title"] and data["text"]
        assert data["clauses"] and len(data["qa"]) == 3
        if data["id"] == "nda":
            assert "Hidden Customer Exception" not in data["text"]
            assert any(label["match"] == "4. Additional Permitted Disclosures"
                       for label in data["clauses"])
        for label in data["clauses"]:
            assert label["expected_risk"] in {"High", "Medium", "Low"}
            assert data["text"].count(label["match"]) == 1
        for missing in data["expected_missing"]:
            assert missing["name"] and missing["aliases"]
        for qa in data["qa"]:
            assert qa["question"] and qa["evidence"] in data["text"]
            assert qa["must_include"] and all(group and all(group) for group in qa["must_include"])
