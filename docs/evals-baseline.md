# Evaluation baseline (2026-10-08)

First full run of `backend/evals` against the Azure deployment (gpt-5-mini, text-embedding-3-small, Azure AI Search, k=4, 3 stability runs). Thresholds in `backend/evals/thresholds.json` are regression floors set just below this baseline.

**Findings:** the analyzer is conservative: no false High flags (precision 1.0) but it misses 4 of 13 labelled High-risk clauses (recall 0.69): a warranty that disclaims legality and correctness (rated Low), an asymmetric auto-renewal notice (Low), and vague payment and termination terms (Medium). Q&A retrieval, keyword correctness and groundedness were all 1.0, so the Q&A set is too easy and should get harder questions.


Time: 2026-10-08T13:07:22.430642+00:00 UTC  |  Duration: 1230.6s  |  Git: 8a68244  |  Model: gpt-5-mini

## Aggregate metrics

| Metric | Value | Threshold | Result |
|---|---:|---:|---|
| risky_precision | 1.000 | 0.6 | PASS |
| risky_recall | 0.692 | 0.7 | FAIL |
| risky_f1 | 0.818 | — | PASS |
| exact_level_accuracy | 0.830 | — | PASS |
| within_one_level_accuracy | 0.957 | — | PASS |
| missing_recall | 0.750 | 0.6 | PASS |
| retrieval_hit_rate | 1.000 | 0.8 | PASS |
| answer_correctness | 1.000 | 0.7 | PASS |
| groundedness | 1.000 | 0.8 | PASS |
| max_score_range | 0.000 | 15 | PASS |

Overall: **FAIL**

## Service Agreement (bad)

| Metric | Value |
|---|---:|
| risky_precision | 1.000 |
| risky_recall | 0.571 |
| risky_f1 | 0.727 |
| exact_level_accuracy | 0.750 |
| within_one_level_accuracy | 0.917 |
| matched_clauses | 12.000 |
| tp | 4.000 |
| fp | 0.000 |
| fn | 3.000 |
| exact | 9.000 |
| near | 11.000 |
| count | 12.000 |
| missing_recall | 1.000 |
| missing_hits | 0.000 |
| missing_expected | 0.000 |
| retrieval_hit_rate | 1.000 |
| answer_correctness | 1.000 |
| groundedness | 1.000 |

| Clause | Expected | Predicted |
|---|---|---|
| 1. Work | Medium | Medium |
| 2. Payment | High | Medium |
| 3. Timeline | Medium | Medium |
| 4. Changes | Medium | Medium |
| 5. Ownership | High | High |
| 6. Confidentiality | High | High |
| 7. Termination | High | Medium |
| 8. Liability | High | High |
| 9. Warranties | High | Low |
| 10. Disputes | Medium | Medium |
| 11. Governing Law | Medium | Medium |
| 12. Entire Agreement | High | High |

| Question | Retrieval | Keywords | Grounded |
|---|---|---|---|
| What payment amount is agreed? | True | True | True |
| Who owns the project work? | True | True | True |
| Can either party terminate? | True | True | True |

## Software Development Services Agreement (good)

| Metric | Value |
|---|---:|
| risky_precision | 1.000 |
| risky_recall | 1.000 |
| risky_f1 | 1.000 |
| exact_level_accuracy | 1.000 |
| within_one_level_accuracy | 1.000 |
| matched_clauses | 11.000 |
| tp | 0.000 |
| fp | 0.000 |
| fn | 0.000 |
| exact | 11.000 |
| near | 11.000 |
| count | 11.000 |
| missing_recall | 1.000 |
| missing_hits | 0.000 |
| missing_expected | 0.000 |
| retrieval_hit_rate | 1.000 |
| answer_correctness | 1.000 |
| groundedness | 1.000 |

| Clause | Expected | Predicted |
|---|---|---|
| 1. Services | Low | Low |
| 2. Payment | Low | Low |
| 3. Delivery and Acceptance | Low | Low |
| 4. Intellectual Property | Low | Low |
| 5. Confidentiality | Low | Low |
| 6. Liability | Low | Low |
| 7. Termination | Low | Low |
| 8. Dispute Resolution | Low | Low |
| 9. Governing Law | Low | Low |
| 10. Warranties | Low | Low |
| 11. Entire Agreement | Low | Low |

| Question | Retrieval | Keywords | Grounded |
|---|---|---|---|
| When are invoices payable? | True | True | True |
| Who owns custom deliverables? | True | True | True |
| What law governs? | True | True | True |

## Freelance Development Agreement (incomplete)

| Metric | Value |
|---|---:|
| risky_precision | 1.000 |
| risky_recall | 1.000 |
| risky_f1 | 1.000 |
| exact_level_accuracy | 0.429 |
| within_one_level_accuracy | 1.000 |
| matched_clauses | 7.000 |
| tp | 0.000 |
| fp | 0.000 |
| fn | 0.000 |
| exact | 3.000 |
| near | 7.000 |
| count | 7.000 |
| missing_recall | 0.750 |
| missing_hits | 3.000 |
| missing_expected | 4.000 |
| retrieval_hit_rate | 1.000 |
| answer_correctness | 1.000 |
| groundedness | 1.000 |

| Clause | Expected | Predicted |
|---|---|---|
| 1. Work | Low | Low |
| 2. Payment | Low | Low |
| 3. Timeline | Medium | Low |
| 4. Intellectual Property | Medium | Low |
| 5. Confidentiality | Medium | Low |
| 6. Termination | Low | Medium |
| 7. Governing Law | Low | Low |

| Question | Retrieval | Keywords | Grounded |
|---|---|---|---|
| How much is the project fee? | True | True | True |
| When is the target completion date? | True | True | True |
| What is the termination notice? | True | True | True |

## Mutual Non-Disclosure Agreement (nda)

| Metric | Value |
|---|---:|
| risky_precision | 1.000 |
| risky_recall | 1.000 |
| risky_f1 | 1.000 |
| exact_level_accuracy | 1.000 |
| within_one_level_accuracy | 1.000 |
| matched_clauses | 8.000 |
| tp | 3.000 |
| fp | 0.000 |
| fn | 0.000 |
| exact | 8.000 |
| near | 8.000 |
| count | 8.000 |
| missing_recall | 1.000 |
| missing_hits | 0.000 |
| missing_expected | 0.000 |
| retrieval_hit_rate | 1.000 |
| answer_correctness | 1.000 |
| groundedness | 1.000 |

| Clause | Expected | Predicted |
|---|---|---|
| 1. Purpose | Low | Low |
| 2. Confidential Information | Low | Low |
| 3. Use and Disclosure | Low | Low |
| 4. Additional Permitted Disclosures | High | High |
| 5. Duration | High | High |
| 6. Return of Materials | Low | Low |
| 7. Liability | High | High |
| 8. Governing Law | Low | Low |

| Question | Retrieval | Keywords | Grounded |
|---|---|---|---|
| May Harbor Labs share customer lists with prospects? | True | True | True |
| How long do Northstar duties survive? | True | True | True |
| When must materials be returned? | True | True | True |

## SaaS Subscription Agreement (saas)

| Metric | Value |
|---|---:|
| risky_precision | 1.000 |
| risky_recall | 0.667 |
| risky_f1 | 0.800 |
| exact_level_accuracy | 0.889 |
| within_one_level_accuracy | 0.889 |
| matched_clauses | 9.000 |
| tp | 2.000 |
| fp | 0.000 |
| fn | 1.000 |
