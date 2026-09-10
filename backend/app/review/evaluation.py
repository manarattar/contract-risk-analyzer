"""Deterministic evaluation utilities. No provider calls or invented labels."""
import json
import math
from pathlib import Path


def measures(predicted_ids, expected_ids, supported_claims, total_claims, correct_citations, total_citations):
    predicted, expected = set(predicted_ids), set(expected_ids)
    true_positive = len(predicted & expected)
    return {
        "finding_precision": true_positive / len(predicted) if predicted else None,
        "finding_recall": true_positive / len(expected) if expected else None,
        "unsupported_claim_rate": 1-supported_claims/total_claims if total_claims else None,
        "citation_accuracy": correct_citations/total_citations if total_citations else None,
        "counts": {"predictions": len(predicted), "expected": len(expected), "matched": true_positive,
                   "claims": total_claims, "citations": total_citations},
    }


def release_gate(report):
    reasons = []
    reviewers = report.get("qualified_reviewers", [])
    if report.get("reviewer_adjudicated") is not True or not isinstance(reviewers, list) or len({v.strip() for v in reviewers if isinstance(v, str) and v.strip()}) < 2:
        reasons.append("Independent qualified adjudication is missing.")
    held_out = report.get("held_out_families")
    if type(held_out) is not int or held_out < 40:
        reasons.append("The frozen held-out corpus is incomplete.")
    if not all(report.get(key) for key in ["dataset_hash", "prompt_hash", "model_version", "parser_version"]):
        reasons.append("Version provenance is incomplete.")
    metrics = report.get("metrics", {})
    for key, threshold in [("citation_accuracy", .99), ("finding_precision", .90), ("finding_recall", .90)]:
        value = metrics.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not threshold <= value <= 1:
            reasons.append(f"{key} gate is not met.")
    unsupported = metrics.get("unsupported_claim_rate")
    if isinstance(unsupported, bool) or not isinstance(unsupported, (int, float)) or not math.isfinite(unsupported) or not 0 <= unsupported <= .01:
        reasons.append("Unsupported-claim gate is not met.")
    if type(report.get("critical_failures")) is not int or report["critical_failures"] != 0:
        reasons.append("Critical failure gate is not met.")
    return {"eligible": not reasons, "reasons": reasons}


if __name__ == "__main__":
    import sys
    result = release_gate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["eligible"] else 1)
