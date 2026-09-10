# Evaluation and test plan

Current results below are observed. All other tests, datasets, thresholds and performance budgets are proposed and have not been executed.

## Recorded safe checks

| Check | Result | Limits |
|---|---|---|
| Repository identity/status | HEAD `6bbcd0e8af6deff14e5a6d97b4da23e21fb6861e`; pre-existing `.gitignore` modification | Repository, not deployed artifact |
| Backend existing offline suite | **23 passed, 13 deselected, 3 warnings**, 14.31 s test-reported runtime | Includes in-memory synthetic mock PDF generation; not source fidelity or real LLM evaluation |
| Frontend existing lint | **Failed: 128 errors, 0 warnings**, exit 1 | Mostly `react/prop-types`; also unused `SORT_FIELDS` and unescaped apostrophe. Does not measure runtime functionality |
| Source/route inventory | Frontend/backend/services/tests/container/deployment source inspected; no applicable AGENTS.md found | Excluded dependency internals, secrets, local data and existing contract files |
| Deliverable static verification | 77 audit code references resolved with line numbers within file bounds; all local Markdown links resolve; HTML has 37 unique IDs, 43 valid anchor links, all six screens, balanced tags, zero scripts/external assets | Structural checks only; wireframes were not browser-rendered or screen-reader tested |

Backend command, run from `backend` using its existing venv:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.\venv\Scripts\python.exe -B -m pytest tests/test_calibration.py -m 'not integration' -p no:cacheprovider -q
```

Warnings are unregistered `pytest.mark.integration` at test lines 157, 200 and 248. Reviewed test bodies before execution: selected tests use pure helpers/mock fixtures and an in-memory report buffer. Deselected integration classes call the real provider and were not run. Mock mode alone is not a sufficient safeguard because those integration classes directly call `analyze_contract`.

Frontend command from `frontend`: `npm run lint -- --no-cache`. No `--fix`, installation or build was run. Existing dependencies were used. No application server, database writes, Chroma operations, embedding downloads, uploads, paid API calls, production requests or migrations were performed. No confidential contracts or stored contract artifacts were read.

Not measured: deployed security/headers/permissions, actual provider/model configuration, legal quality, latency/throughput/cost, runtime accessibility, parser adversarial behavior, export visual/tag quality, live retrieval precision or full deletion. No production-ready/compliant/legal-accuracy claim follows from the unit results.

## Evaluation corpus proposal

Start with 120 synthetic or explicitly licensed/non-confidential contract families, each with a context record and label provenance. Split by family/template, never by chunk: 60 development, 20 validation, 40 held-out. Keep variants of the same agreement (including translated/perturbed/scanned forms and comparison pairs) in the same split. Store hashes and usage rights. Do not automatically use production uploads or feedback text for training/evaluation.

Primary scope: English services/software agreements. Include balanced, one-sided, incomplete and ambiguous terms; role reversal; unknown jurisdiction; repeated definitions/clauses; missing schedules; cross-references and mutually qualifying terms. Include enough high-impact issues that aggregate easy clauses cannot dominate results. Additional types/languages are out-of-scope challenge slices until separately approved, not pooled into pilot pass rates.

Document variants: digital PDF, multi-column pages, TXT with line breaks/encoding issues, DOCX with tables/headers/footnotes, long clauses, 1/10/50/200 pages, image-only/mixed scans, malformed/truncated/encrypted documents and duplicated uploads. Synthetic injection variants place instructions in visible text, small/overlaid text, metadata, tables and questions. Safe archive-limit fixtures exercise bounds without executing malware or uncontrolled resource exhaustion.

Each family has independently authored expected clauses, exact page/block/character spans, complete/missing/uncertain coverage labels, permitted interpretations, inappropriate claims, contextual impact and business preference. Include supported/unanswerable/multi-hop questions and comparison pairs with substantive/cosmetic/moved/split/merged clauses. Human-authored counterexamples matter more than model-generated labels accepted without review.

## Labels and adjudication

Two independent qualified contract reviewers label issue presence, support, consequence, acceptable alternative wording and legal-context limits; disagreements go to a third adjudicator. A document engineer labels extraction order/coverage/spans. Keep reviewer identity/qualification in restricted metadata, label version, rationale, unresolved disagreement and uncertainty. Report agreement (e.g. Cohen's kappa on categorical labels and span overlap) before adjudication; do not force genuinely ambiguous cases into binary truth.

Rubric distinguishes objective text facts, contextual interpretations, business preferences and unsupported legal conclusions. A revision can have multiple acceptable forms; grade preservation of meaning, introduced obligations, scope changes and usefulness, not exact wording. Contradiction labels must cite both provisions and relevant exceptions. Absence labels need scope/coverage and the playbook expectation, not invented citations.

Freeze held-out data behind an evaluation owner. AI engineers may inspect development/validation cases but not tune prompts on held-out failures. A failed held-out release requires a new candidate and controlled rerun; rotate/expand held-out cases if repeated exposure contaminates them. Log every evaluation release, prompt hash, model/provider/version/parameters, parser/OCR/embedding artifacts, retrieval settings, code revision, dataset manifest/hash and run date. Provider model alias drift is a re-evaluation trigger.

## Metrics, matching and proposed gates

Use document-family bootstrap confidence intervals and provide raw numerators/denominators, per-slice counts and worst-case examples. Small samples do not establish safety: if a slice has fewer than 20 relevant examples, collect more rather than claim a broad pass. Abstained and failed documents remain in coverage/reliability denominators, so withholding all answers cannot win the quality metric.

| Metric | Definition | Proposed controlled-pilot gate |
|---|---|---|
| Extraction text fidelity | Normalized correct characters/tokens vs labelled readable content; report order/table-cell errors separately | ≥99% on supported digital slice; no omitted material provision; unreadable inputs always flagged |
| Clause extraction precision/recall | One-to-one matching by source-span overlap (IoU ≥0.8) and reviewer-approved boundaries | ≥95% precision and recall, with short/preamble/table slices reported |
| Citation existence/location | Span belongs to exact document version and quote maps to source | 100%; zero wrong-document/version citations |
| Citation support correctness | Cited evidence entails the attached factual claim under context, reviewer-adjudicated | ≥99% point estimate; lower 95% interval ≥97% after sufficient sample |
| Finding precision | Matched supported predicted findings / all predicted findings; deduplicate by issue and source | ≥90%; lower 95% interval ≥85% |
| Finding recall | Matched labelled issues / all in-scope labelled issues, including failures/abstentions | ≥90% overall; ≥95% high-impact with lower 95% interval ≥90%; zero missed critical release-blocking fixtures |
| Unsupported-claim rate | Unsupported factual/legal assertions / all generated factual/legal assertions, including revisions and summary | ≤1%; zero fabricated legal authorities or signing assurances |
| Retrieval recall@k | Questions whose labelled supporting spans appear in retrieved context / answerable questions | ≥95% at selected k/token budget; report multi-hop separately |
| Abstention correctness | Unsupported/insufficient-context questions correctly withheld / such questions | ≥95%; separately report answer coverage and unnecessary abstention rate |
| Contradiction quality | Precision/recall of paired conflicting spans, including exception handling | ≥90% precision; no reassuring result when contradiction stage fails |
| Comparison alignment | Correct many-to-many clause links / adjudicated links; substantive-change recall | ≥95% alignment precision; ≥95% high-impact change recall before capability enabled |
| Revision usefulness/safety | Reviewer grade 1–5 plus unsupported obligations/meaning changes | Median ≥4; zero unflagged critical changes introduced by suggestions |
| Reviewer task usefulness | Blinded paired manual/assisted task completion and correction burden | Median usefulness ≥4/5; no increased high-impact miss rate; time improvement secondary |

These proposed thresholds are engineering go/no-go hypotheses to ratify with qualified reviewers and risk owners. They are not legal accuracy guarantees. “Zero observed” is bounded by sample size and must be accompanied by an interval or sample count. High-severity qualitative failures override aggregate scores. Use [NIST's Generative AI Profile](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) as lifecycle risk-management guidance, not certification.

## Test layers and negative cases

| Layer | Required coverage | Trigger / owner |
|---|---|---|
| Pure unit | Span mapping, count/ID validation, split coverage, safe escaping, state machine, metric matching | Every PR; engineering |
| Parser fixtures | Digital/scanned/table/long/empty/truncated files with expected coverage | Parser/config change; document engineer |
| API isolation | Anonymous and two-tenant matrix on upload/status/analysis/pages/QA/compare/export/retry/cancel/delete/library/decisions | Every route change; security |
| Jobs/transactions | Restart after each boundary, duplicate deliveries, rollback, vector outage, provider timeout, cancelled/deleted late commit | Worker/storage change; backend |
| Retrieval/AI offline | Stub gateway, no network, empty/error retrieval, hallucinated/reordered citations, malformed JSON, prompt injection | Every AI change; AI engineer |
| Opt-in live evaluation | Frozen corpus only, approved provider and explicit spend cap; never real confidential contracts | Release candidate/model change; evaluation owner, separate authorization |
| UX/accessibility | File picker, errors, resume, evidence/back navigation, decision save/conflict, compare and delete confirm | Component changes + release; frontend/accessibility |
| Export | Snapshot equality, escaping, long rows, special characters, reading order, source/provenance labels, deletion/expiry | Export change; document/accessibility |
| Operations | Build context, dependency advisory disposition, schema migration/rollback, readiness, restore/tombstone replay | Release; platform/security |

Authorization matrix must include guessed valid IDs, mixed-own/foreign comparison pairs, foreign nested source-span IDs, revoked memberships and owner changes mid-request. Unauthorized requests must neither trigger provider use nor disclose object existence. Access validation occurs before cache/index reads.

Deletion race matrix covers before upload commit, during parse, during model request, after indexing, during export and during backup restore. Test retrying each failed purge store independently. No real deletion was attempted in this audit.

## Accessibility and wireframe verification

For implementation, test keyboard plus a real screen reader/browser pair (e.g. NVDA/Firefox and VoiceOver/Safari as available), visible focus and focus restoration. Use 320, 375, 768 and 1440 CSS px; 200%/400% zoom; increased text spacing; high contrast and reduced motion. Automated accessibility checks supplement manual tasks and cannot establish conformance alone. Verify source highlights have equivalent text and location announcements, table semantics survive reflow and background polling does not steal focus.

Wireframes are static HTML/CSS specifications, not application behavior. All six screens are present in one file with anchors, native disclosures, forms and breakpoint adaptations. Action buttons intentionally disabled where saving/uploading/exporting/deleting would otherwise be implied. State annotations describe required implementation. No script/CDN/assets/network dependencies are needed. Browser/screen-reader validation results, if any, must be recorded explicitly; static inspection alone is not a visual accessibility pass.

## Performance and cost protocol

Staging only, synthetic corpus, gateway stub by default. Record hardware, browser, network profile, worker memory/CPU, warm/cold embedding state, concurrency and page/token distribution. Proposed pilot load: 5 concurrent processing jobs and 20 active reviewers; tests must remain within sandbox capacity. Record upload memory, parser/OCR time, queue wait, model latency, indexing and first usable evidence, separately from page load.

Initial product budgets: digital ≤10 pages p95 upload-commit→ready ≤120 s; page/evidence navigation p95 ≤300 ms after data available; API non-AI reads p95 ≤500 ms; no unbounded DOM growth or timers after navigation. Test 50-page support boundary and reject 200 pages until expanded capability passes. Track failure/partial counts, not only successful timings.

For page experience, measure field p75 LCP ≤2.5 s, INP ≤200 ms and CLS ≤0.1 separately by mobile/desktop; lab proxies do not replace field INP. These thresholds follow [Core Web Vitals](https://web.dev/articles/vitals). They do not measure AI processing time. Cost includes retries and failed attempts; provider prices are selected and verified at implementation time, not assumed here.

## Change and release governance

Changes to model, prompt, parser, OCR, chunking, retrieval, schema or playbook require a new version and relevant held-out evaluation. Compare against previous candidate per slice; prohibit silent downgrade in evidence fidelity. Store minimized evaluation outputs and adjudications under approved access/retention. Capture user corrections only with permission and provenance; local thumbs ratings are not ground truth.

Release decision attaches test output, quality metrics/intervals, known limitations, security/accessibility review, provider/privacy approval and rollback version. Pilot owner may narrow supported scope but cannot waive cross-tenant leakage or fabricated-evidence failures. See [backlog](implementation-backlog.md) for phase gates and stop conditions.
