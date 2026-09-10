# Implementation backlog and release gates

Planning only. Effort is person-days (PD), includes implementation and targeted verification, excludes procurement/legal review waiting time and unknown legacy migration/data cleanup. Ranges are estimates, not commitments. Engineering, product, AI quality, security and accessibility reviewers are required roles; no agents or implementation work were dispatched in this audit.

P0 blocks confidential pilot use. P1 is needed to offer its named capability dependably; disable unfinished capabilities rather than implying they work. P2 broadens scope only after measured pilot success. Proposed baseline scope is in [product-spec.md](product-spec.md).

## Ordered work packages

| ID / priority | Work / audit links | Dependencies | Affected components / lead | Effort |
|---|---|---|---|---|
| B01 · P0 | Explicit demo and failure semantics; F02–F04 | None | config, schemas, upload/QA, analyzer, UI/report; AI + full-stack | 3–5 PD |
| B02 · P0 | Identity, ownership, quotas, role checks; F01/F14 | None; membership/provider decisions | DB, all routes, storage/retrieval adapters, session UX; security + backend | 7–12 PD |
| B03 · P0 | Bounded quarantine ingestion and output containment; F11/F12/F19/F24 | B02 for quotas; infrastructure sandbox capability | upload/compare, parser/export boundaries, proxy/containers; security + backend | 6–10 PD |
| B04 · P0 | Source-preserving extraction and coverage; F06–F08 | B03; source data contract | parsers, splitter, schemas, document rendering API; document-AI | 10–18 PD |
| B05 · P0 | Durable jobs, transactions and resumable status; F13/F16/F24 | B02/B03; job schema | database, workers, object/index adapters, App/api polling; backend | 7–12 PD |
| B06 · P0 | Grounded AI pipeline and abstention; F02/F04/F05/F08/F10 | B01/B04/B05; B09 fixture design starts first | prompts, analyzer, vector store, QA/schema validator; AI | 10–18 PD |
| B07 · P0 | Retention and verified full deletion; F14 | B02/B05; approved provider/storage inventory | all stores, jobs, settings, deletion UI/receipts; security + backend | 5–9 PD |
| B08 · P0 | Context, library, accessible evidence review and decisions; F08/F09/F16–F18 | B02/B04/B05/B06; prototype can precede API completion | App, routes, Clause/Chat components, new decision model; product + frontend | 12–20 PD |
| B09 · P0 | Adjudicated evaluation and safety gate; F05–F10/F23 | Start immediately; final run after B04/B06 | test harness, datasets, evaluation manifests; AI + qualified reviewers | 8–15 engineering PD + 8–16 reviewer PD |
| B10 · P0 | CI, dependencies, deployment truth and recovery; F21–F24 | Start immediately; gate after B02–B07 | CI, requirements/locks, containers, migrations, monitoring/runbooks; platform | 5–9 PD |
| B11 · P1 | Substantive comparison; F15 | B04/B06/B08/B09 | comparison schema/service/view, alignment UI; AI + product | 8–14 PD |
| B12 · P1 | Reviewed export with provenance/accessibility; F19/F20 | B03/B07/B08 | report generator, export jobs/storage and UI; full-stack + accessibility | 5–9 PD |
| B13 · P1 | Performance, cost and operational tuning; F16/F24 | B05/B06/B08, pilot telemetry | gateway, workers, rendering, retrieval, telemetry; platform + frontend | 4–8 PD |
| B14 · P1 | Gated OCR and advanced layouts | B03/B04/B09, provider/privacy review if external OCR | parser/OCR pipeline, quality UI, corpus; document-AI | 8–15 PD |
| B15 · P2 | Additional approved types/languages and playbooks | B09 + stable pilot metrics | context/rules/evaluation/localization; product + legal/AI | 10–20 PD per bounded expansion |
| B16 · P2 | Team review assignments and richer collaboration | B02/B07/B08 | membership, decisions, conflict UI; full-stack | 5–9 PD |

P0 subtotal: approximately 73–128 engineering PD plus 8–16 reviewer PD. P1 subtotal: 25–45 PD without OCR, 33–60 with OCR. Parallel staffing can shorten calendar time but not remove dependencies or reviewer gates. Re-estimate after B03/B04 technical spikes using synthetic files; do not promise an end date from these ranges.

## Acceptance criteria and verification per package

### B01 — trustworthy states

Demo mode is explicit configuration with synthetic fixtures only, visible on every screen/response/export. Missing live configuration fails startup or disables analysis, never silently generates demo results. No relevant evidence returns a factual abstention; retrieval outages are distinct technical failures. Unanalyzed clauses have impact “not assessed”; contradiction service failure is visible as incomplete. Remove automated signing recommendations and ungrounded legal confidence from pilot output even before the complete B08 redesign.

Tests: mock/live configuration matrix, retrieval empty/error, provider failure, partial batch, report of incomplete contradiction stage. Assert no canned payment/termination statement and no Low-risk default is returned on failure. Zero such paths is the release gate.

### B02 — ownership everywhere

Every existing and new route authenticates and authorizes the exact record; comparison checks both operands before any source read/provider call. Library, pages, status, analysis, QA, export, retry, cancel and deletion are covered. Owner/workspace IDs come from trusted session, not user payload. Unauthorized responses reveal no filename/content. Quotas apply before parsing/provider use. Define invite-only roles: viewer reads, reviewer records decisions/requests exports, owner/admin manages retention/deletion; explicit policy controls upload.

Tests: two tenants plus anonymous caller against every endpoint and nested ID; mixed-owner comparison; revoked membership and expired session; CSRF if cookies; rate-limit exhaustion without paid calls. Gate: zero cross-tenant reads/writes or provider requests from denied actions.

### B03 — ingestion/output boundary

Stream limit rejects over-budget bytes before full buffering; compare enforces per-file and aggregate caps. Storage keys contain no supplied filename. Format/signature, DOCX expansion and parser budgets are enforced, quarantined assets cannot be downloaded, sandbox has no network. Escape export text and encode download filenames. If PDF export cannot yet be safely contained, disable it until B12.

Tests: missing/wrong Content-Length, chunked oversize, filename traversal/control characters, extension/signature mismatch, malformed/oversized ZIP metadata, safe embedded relationship fixture, empty files, parser timeout and malicious-looking markup treated as text. Gate: bounded resource use, no external fetch and no path escape in isolated synthetic tests.

### B04 — extraction with provenance

Every readable block maps to an immutable source version and order. Preserve preamble, short clauses, table cells, definitions and cross-references; no omitted text silently disappears. PDF spans map to pages/boxes; DOCX spans use blocks/cells with rendered-view labels. Empty/poor scans produce explicit unavailable/partial states. Completeness warnings identify missing/uncertain pages without asserting facts unavailable from the file.

Tests: short headings/preamble, very long sentence, repeated clauses, multi-column PDF, DOCX tables/headers/footnotes, page-only images, encoding corruption, rotated text, 50-page limit and late-page provisions. Gate: corpus extraction and citation targets in evaluation plan; no complete result for unreadable fixture.

### B05 — durable lifecycle

Committed job survives worker restart, retries within budget, has an explicit terminal state and resumes without duplicate analysis. Each worker owns its session and rolls back failures. Atomic DB job/outbox write and reconciliation handle orphan files/indexes. Cancel/delete epochs block late result commits. UI restores job identity after refresh, cleans polling and distinguishes network disconnection from job failure.

Tests: kill worker between each stage/commit, duplicate delivery, lost enqueue, SQLite-to-target migration rehearsal with synthetic data, DB commit/vector outage, same idempotency key, cancel during provider response, deleted document retry. Gate: no indefinitely processing fixture or duplicate billed operation under simulated gateway; agreed recovery target met.

### B06 — grounded output

Every non-absence finding and factual answer carries verified spans from the correct version. Exact input IDs/counts are validated; reordered/extra/missing items cannot be silently accepted. Summary and contradiction status expose coverage. Retrieval honors version and ownership and can abstain. Prompts are versioned data-boundary instructions with no tools or arbitrary URL fetch. Legal claims beyond supplied context are withheld; revisions expose assumptions and remain drafts.

Tests: empty/wrong retrieval, fabricated citations, repeated text, injection in clause/header/question, contradictions whose exceptions occur after 600 characters, reordered batch outputs, unsupported jurisdiction, edited context. Gate: held-out evidence/claim thresholds plus zero wrong-document citations; no inferred “safe to sign.”

### B07 — full deletion and provider policy

Approved provider/storage inventory and privacy copy precede confidential use. Tombstone immediately revokes access. Purge originals, derivatives, chunks, vectors, analyses, QA, comparisons, exports, temp files and caches; provider and backup exceptions visible. Repeated deletion is idempotent; receipt distinguishes completed, pending and failed stores. Restore replays deletion records before serving.

Tests: delete during upload/parse/inference/export, repeated/foreign delete, one failed store and retry, comparison references, expired exports, restore from synthetic backup. Gate: active purge within approved SLA, no retrieval after tombstone, no resurrection. Security reviewer signs evidence and any permitted exception.

### B08 — actual human review

Upload captures confirmed/unknown context and privacy before transmission. Library supports recoverable errors and returning to versions. Every finding offers evidence navigation, accept/dismiss/edit/annotate/escalate with saved provenance and conflict handling. No unsupported score dashboard or winner. Mobile preserves both evidence and detail. Keyboard/screen-reader users can finish the same journeys; errors never discard drafts.

Tests: moderated synthetic workflows, keyboard-only, screen reader, 320/375/768/1440 px, 200%/400% zoom, reduced motion, slow/offline response, conflicting decision edits. Gate: zero critical journey blockers; persisted decision survives refresh and is tied to correct run/span.

### B09 — credible measurement

Versioned manifest, independent labels, adjudication, split by template family and frozen held-out set. Track extraction, citation support, finding precision/recall, unsupported claims, abstention coverage and usefulness. Treat existing score tests as regression checks only. Register integration marker; default suite never makes provider calls. New live evaluations require a separate explicit budget/authorization outside this audit.

Tests: harness seed/reproducibility, split leakage checks, metric denominator tests, unavailable-output accounting, duplicate prediction matching. Gate: all proposed pilot thresholds met with counts/confidence intervals, no masked high-severity miss; qualified reviewer approval of scoped use.

### B10 — operational release gate

CI runs safe unit/security/schema checks and frontend lint/build from locked dependencies, without real data or live API credentials. Resolve current 128 lint errors appropriately rather than blindly disabling the rules. Add transitive backend lock/hash, SBOM and dependency-advisory triage. Reconcile actual SQLite/Postgres deployment and frontend origin. Build excludes secrets/data/venv; migrations and rollback rehearsed. Monitor queue/coverage/purge/cost; readiness probes use no paid API. Restore and incident runbooks have named owners.

Tests: clean checkout CI, offline live-call guard, image-content check, staging same-origin API, configuration fail-fast, migration rollback, restore with tombstones, alert exercise. Gate: passing reproducible CI, reviewed vulnerability disposition and demonstrated RPO/RTO; no claim that dependency age alone proves a CVE.

### B11 — comparison

All repeated/split/merged clauses are alignable. Exact text changes and substantive actor/duty/amount/deadline/exception differences are shown with two-version evidence. Uncertain alignment is labelled and editable; no score winner or score-based unchanged status.

Tests: same text/different score, changed liability cap/same score, deletion, renumbering, moved schedule, repeated payment clauses, split merger and one unreadable version. Gate: adjudicated alignment/substantive-change targets and no “unchanged” on critical changed fixture.

### B12 — export

Export preview reflects immutable review snapshot, scope, unresolved items, source references, decisions and pipeline versions. Default accessible HTML; safe PDF optional. Export is authorized/expiring/deletable. No contract/model text is executed as markup or external resource.

Tests: long/multilingual text, 200 findings, markup/control characters, missing-glyph/page-break checks, keyboard-accessible HTML, PDF reading order/tag verification if offered, foreign/expired URL and deletion. Gate: snapshot matches review and contains no unsupported legal/signing assurance; PDF advertised accessibility only after specialist verification.

### B13–B16 — controlled expansion

B13: measure p50/p95 latency/cost by length, cap spend and concurrency, page lazy rendering, no timer leaks. Tests: reproducible synthetic load, network throttling, cold/warm runs, retry storms and 200-page capability boundary. Accept only with stated load/hardware, no silent truncation and approved cost cap.

B14: OCR preserves page geometry, flags uncertainty, and separately evaluates tables and scanned pages. Test scan noise, rotation, handwriting/out-of-scope pages and mixed PDF; gate on per-slice extraction and evidence quality, not average across easy digital files.

B15: one contract type/language at a time, qualified playbook/adjudication and accessibility/localization review; gate held-out quality for that slice. B16: assignments/notifications only within explicit product permissions, audit history and concurrent edits; test revocation, reassignment and retention. Both require no regression on pilot safety gates.

## Release progression

| Stage | Included scope | Entry/exit evidence | Stop/rollback condition |
|---|---|---|---|
| Synthetic demo | Existing stack, unmistakable demo label; safe fixed fixtures only | B01 containment; avoid arbitrary public ingestion until B02/B03; all mock provenance visible | Any live fallback masquerading as document evidence; disable affected capability |
| Controlled pilot | Invited users, supported digital services agreements, human review, accessible HTML record | All B01–B10 gates pass; B12 minimum safe HTML snapshot if export included; provider/privacy and qualified scope review; initial ≤50 pages, ≤10 MiB; staffed support | Cross-user citation/access, misleading failed/complete state, unsupported critical claim, deletion breach or uncontrolled spend: pause new ingestion, contain and review |
| Expanded pilot | Substantive compare, PDF and/or scans offered only when their gates pass | B11/B12/B14 capability-specific evaluation; B13 performance under proposed 5 concurrent reviews and 20 active readers | Capability regression: disable that capability, preserve source/review versions, revert pipeline version |
| Broader use | Increased users/length, approved types and team workflows | ≥4 weeks stable pilot telemetry (proposal), independent security/accessibility review, restore drill, all quality slices passing with qualified human process | Reopen gates on provider/parser/model changes, leakage, material missed issues or rising unsupported-claim rate |

Open decisions: actual tenant model, provider/data region/terms, precise contract scope/jurisdiction, storage/backup topology, reviewer availability, pilot budget and retention promises. Resolve before their dependent gates. These are not reasons to stop the authorized audit; they are implementation prerequisites.
