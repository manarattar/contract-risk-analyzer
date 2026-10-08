"""Run service-level contract evaluations and write Markdown and JSON reports."""

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import get_settings
from app.services.clause_splitter import split_into_clauses
from app.services.risk_analyzer import analyze_contract, answer_question
from app.services.vector_store import delete_document, search, store_chunks
from evals.judge import groundedness_rate, judge_groundedness
from evals.metrics import (aggregate_metrics, answer_correct, clause_metrics, match_clauses,
                           missing_counts, missing_recall, retrieval_hit, score_stability)

ROOT = Path(__file__).parent


def evaluate(contract, k):
    chunks = split_into_clauses(contract["text"])
    analysis = analyze_contract(chunks, contract["text"])
    metrics = clause_metrics(match_clauses(analysis.clauses, contract["clauses"]))
    metrics["missing_recall"] = missing_recall(contract["expected_missing"], analysis.missing_clauses)
    metrics["missing_hits"], metrics["missing_expected"] = missing_counts(
        contract["expected_missing"], analysis.missing_clauses)
    doc_id = f"eval-{contract['id']}-{uuid4().hex}"
    questions = []
    try:
        store_chunks(doc_id, chunks)
        for item in contract["qa"]:
            sources = search(doc_id, item["question"], k)
            answer = answer_question(item["question"], sources)
            judgment = judge_groundedness(sources, answer)
            questions.append({"question": item["question"], "answer": answer,
                              "retrieval_hit": retrieval_hit(item["evidence"], sources, k),
                              "answer_correct": answer_correct(answer, item["must_include"]),
                              "grounded": judgment["grounded"], "judge_reason": judgment["reason"]})
    finally:
        delete_document(doc_id)
    metrics["retrieval_hit_rate"] = sum(q["retrieval_hit"] for q in questions) / len(questions)
    metrics["answer_correctness"] = sum(q["answer_correct"] for q in questions) / len(questions)
    metrics["groundedness"] = groundedness_rate(questions)
    return {"id": contract["id"], "title": contract["title"], "metrics": metrics,
            "overall_score": analysis.overall_risk_score,
            "clauses": [{"match": label["match"], "expected": label["expected_risk"],
                         "predicted": clause.risk_level.value if clause else "Unmatched"}
                        for label, clause in match_clauses(analysis.clauses, contract["clauses"])],
            "questions": questions}


def render(report):
    lines = ["# Contract evaluation", "", f"Time: {report['timestamp']} UTC  |  Duration: {report['duration_seconds']:.1f}s  |  Git: {report['git_sha']}  |  Model: {report['model']}",
             "", "## Aggregate metrics", "", "| Metric | Value | Threshold | Result |", "|---|---:|---:|---|"]
    for key, value in report["aggregate"].items():
        limit = report["thresholds"].get(key)
        status = "PASS" if report["checks"].get(key, True) else "FAIL"
        lines.append(f"| {key} | {value:.3f} | {limit if limit is not None else '—'} | {status} |")
    lines += ["", f"Overall: **{'PASS' if report['passed'] else 'FAIL'}**", ""]
    for item in report["contracts"]:
        lines += [f"## {item['title']} ({item['id']})", "", "| Metric | Value |", "|---|---:|"]
        lines += [f"| {name} | {value:.3f} |" for name, value in item["metrics"].items()]
        lines += ["", "| Clause | Expected | Predicted |", "|---|---|---|"]
        lines += [f"| {c['match']} | {c['expected']} | {c['predicted']} |" for c in item["clauses"]]
        lines += ["", "| Question | Retrieval | Keywords | Grounded |", "|---|---|---|---|"]
        lines += [f"| {q['question']} | {q['retrieval_hit']} | {q['answer_correct']} | {q['grounded']} |" for q in item["questions"]]
        lines += [""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contracts", nargs="+", default=["all"])
    parser.add_argument("--stability-runs", type=int, default=3)
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--out", type=Path, default=Path("evals/reports"))
    parser.add_argument("--thresholds", type=Path, default=Path("evals/thresholds.json"))
    parser.add_argument("--no-fail", action="store_true")
    args = parser.parse_args()
    if args.stability_runs < 1 or args.k < 1:
        parser.error("--stability-runs and --k must be positive")
    files = sorted((ROOT / "golden").glob("*.json"))
    golden = {item["id"]: item for item in (json.loads(path.read_text(encoding="utf-8")) for path in files)}
    ids = list(golden) if args.contracts == ["all"] else args.contracts
    if any(item not in golden for item in ids):
        parser.error(f"Unknown contract ID; choose from {', '.join(golden)}")
    settings = get_settings()
    if settings.use_mock:
        parser.error("Configure Azure OpenAI or an OpenAI API key; mock mode cannot evaluate model quality")
    started = time.monotonic()
    results = [evaluate(golden[item], args.k) for item in ids]
    scores = [item["overall_score"] for item in results if item["id"] == "bad"]
    if "bad" in ids:
        scores += [analyze_contract(split_into_clauses(golden["bad"]["text"]), golden["bad"]["text"]).overall_risk_score
                   for _ in range(args.stability_runs - 1)]
    stability = score_stability(scores)
    aggregate = aggregate_metrics(results)
    aggregate["max_score_range"] = stability["range"] if scores else 0
    thresholds = json.loads(args.thresholds.read_text(encoding="utf-8"))
    checks = {name: aggregate[name] <= limit if name == "max_score_range" else aggregate[name] >= limit
              for name, limit in thresholds.items()}
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=False)
    report = {"timestamp": datetime.now(timezone.utc).isoformat(), "duration_seconds": time.monotonic() - started,
              "git_sha": sha.stdout.strip() if sha.returncode == 0 else "unavailable",
              "model": (settings.azure_openai_chat_deployment if settings.llm_provider == "azure_openai" else settings.model_name),
              "provider": settings.llm_provider, "k": args.k, "contracts": results, "stability": stability,
              "aggregate": aggregate, "thresholds": thresholds, "checks": checks, "passed": all(checks.values())}
    args.out.mkdir(parents=True, exist_ok=True)
    markdown = render(report)
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.out / "report.md").write_text(markdown + "\n", encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write(markdown + "\n")
    print(markdown)
    return 0 if report["passed"] or args.no_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())

