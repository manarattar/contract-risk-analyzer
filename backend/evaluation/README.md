# Evaluation gate

`release-candidate.json` is deliberately **ineligible**. It does not pretend that synthetic unit tests are adjudicated legal-quality evidence.

Run from `backend`:

```text
python -m app.review.evaluation evaluation/release-candidate.json
```

Exit 1 means the release gate is not met. The detailed corpus, family splits, reviewer adjudication, precision/recall definitions and human review requirements are in `docs/production-readiness/evaluation-and-test-plan.md`. Do not set `REVIEW_EVALUATION_APPROVED=true` based on helper-test success. Version and retain the actual reviewed report before enabling live processing. No evaluation here calls an AI provider.
