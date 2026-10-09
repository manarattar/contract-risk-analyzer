# Evaluation results

All runs use `backend/evals` in GitHub Actions against the Azure deployment (gpt-5-mini 2025-08-07,
text-embedding-3-small, Azure AI Search, k=4, 3 stability runs on the `bad` contract). Full reports
are in this folder.

## 2026-10-09: red-flag prompt calibration

| Metric | Before (`c72f5b7`) | After (`e043af5`) |
|---|---:|---:|
| Risky-clause precision | 1.000 | 0.941 |
| Risky-clause recall | 0.846 | **1.000** |
| Risky-clause F1 | 0.917 | **0.970** |
| Exact risk level | 0.872 | 0.911 |
| Within one level | 0.979 | 1.000 |
| Missing-clause recall | 0.750 | 0.750 |
| Retrieval hit rate@4 | 1.000 | 1.000 |
| Answer correctness | 1.000 | 0.944 |
| Groundedness (LLM judge) | 1.000 | 0.944 |
| Overall score range (3 runs) | 0 | 0 |

**What changed:** the clause prompts only guarded against false positives ("if in doubt, assign
Acceptable Standard"). The new prompts add a list of general red-flag patterns (asymmetric rights,
unilateral price changes, one-sided uncapped liability, disclaimers of core performance, undefined or
discretionary payment, one-sided renewal windows) and limit the guardrail to standard mechanisms.

**Result:** the two clauses the old prompt under-rated (an at-will termination with unclear payment,
an auto-renewal with 90 vs 10 days' notice) are now High. Precision dropped by one false alarm
(a vague governing-law clause rated High instead of Medium).

**Held-out check:** `consulting.json` was added after the first baseline and not used to tune the
prompt. All 3 of its risky clauses were caught (non-compete, discretionary payment withholding,
assignment of pre-existing IP). One pattern in the prompt (discretionary payment) does cover one of
those clauses, so it is not a fully independent test. Its Q&A questions are harder than the rest;
one answer missed the expected detail, which is why answer correctness and groundedness dropped.
The "before" run used 5 contracts (no `consulting.json`), the "after" run 6.

## Pitfall found on the way

The first local baseline (2026-10-08) reported recall 0.69, but it did not measure production: the
local `backend/.env` held a Jev API key, so `_analyze_clauses_batch` used the Jev classifier instead
of the LLM prompt. Production has no Jev key. Evals now run in CI, where the environment matches
production. Lesson: record which code path an eval exercised, not just the score.

## Thresholds

`backend/evals/thresholds.json` holds regression floors: recall 0.9, precision 0.85, missing-clause
recall 0.6, retrieval/answer/groundedness 0.9, score range at most 10 points. The `Evals` workflow
runs on pull requests that touch the analysis code, and on pushes to `eval/*` branches.
