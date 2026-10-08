"""Pure scoring helpers for the golden evaluation set."""

import re
from statistics import pstdev


def normalize(value):
    return " ".join(value.casefold().split())


def match_clauses(clauses, labels):
    matches = []
    for label in labels:
        needle = normalize(label["match"])
        found = [clause for clause in clauses if needle in normalize(clause.original_text)]
        matches.append((label, found[0] if len(found) == 1 else None))
    return matches


def clause_metrics(matches):
    tp = sum(label["expected_risk"] == "High" and clause is not None and clause.risk_level.value == "High" for label, clause in matches)
    fp = sum(label["expected_risk"] != "High" and clause is not None and clause.risk_level.value == "High" for label, clause in matches)
    fn = sum(label["expected_risk"] == "High" and (clause is None or clause.risk_level.value != "High") for label, clause in matches)
    precision = tp / (tp + fp) if tp + fp else 1.0 if not fn else 0.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    levels = {"Low": 0, "Medium": 1, "High": 2}
    exact = sum(clause is not None and clause.risk_level.value == label["expected_risk"] for label, clause in matches)
    near = sum(clause is not None and abs(levels[clause.risk_level.value] - levels[label["expected_risk"]]) <= 1 for label, clause in matches)
    count = len(matches)
    return {"risky_precision": precision, "risky_recall": recall,
            "risky_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            "exact_level_accuracy": exact / count if count else 1.0,
            "within_one_level_accuracy": near / count if count else 1.0,
            "matched_clauses": sum(clause is not None for _, clause in matches),
            "tp": tp, "fp": fp, "fn": fn, "exact": exact, "near": near, "count": count}


def missing_counts(expected, missing):
    predicted = [normalize(f"{item.clause_type} {item.reason}") for item in missing]
    hits = sum(
        any(
            any(re.search(r"(?<!\w)" + re.escape(normalize(alias)) + r"(?!\w)", item)
                for alias in target["aliases"])
            for item in predicted
        )
        for target in expected
    )
    return hits, len(expected)


def missing_recall(expected, missing):
    hits, total = missing_counts(expected, missing)
    return hits / total if total else 1.0


def aggregate_metrics(results):
    metrics = [item["metrics"] for item in results]
    totals = {name: sum(item[name] for item in metrics)
              for name in ("tp", "fp", "fn", "exact", "near", "count",
                           "missing_hits", "missing_expected")}
    tp, fp, fn = totals["tp"], totals["fp"], totals["fn"]
    precision = tp / (tp + fp) if tp + fp else 1.0 if not fn else 0.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    questions = [question for item in results for question in item["questions"]]
    return {"risky_precision": precision, "risky_recall": recall,
            "risky_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            "exact_level_accuracy": totals["exact"] / totals["count"] if totals["count"] else 1.0,
            "within_one_level_accuracy": totals["near"] / totals["count"] if totals["count"] else 1.0,
            "missing_recall": totals["missing_hits"] / totals["missing_expected"]
            if totals["missing_expected"] else 1.0,
            "retrieval_hit_rate": sum(q["retrieval_hit"] for q in questions) / len(questions) if questions else 1.0,
            "answer_correctness": sum(q["answer_correct"] for q in questions) / len(questions) if questions else 1.0,
            "groundedness": sum(q["grounded"] for q in questions) / len(questions) if questions else 1.0}


def retrieval_hit(evidence, chunks, k):
    return any(normalize(evidence) in normalize(chunk) for chunk in chunks[:k])


def answer_correct(answer, groups):
    value = normalize(answer)
    return all(any(normalize(word) in value for word in group) for group in groups)


def score_stability(scores):
    return {"min": min(scores), "max": max(scores), "range": max(scores) - min(scores),
            "stdev": pstdev(scores)} if scores else {"min": None, "max": None, "range": None, "stdev": None}
