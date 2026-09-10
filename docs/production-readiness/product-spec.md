# Proposed product specification

Status: proposed, not implemented. Related evidence: [audit](audit.md), especially F02–F09 and F15–F20.

## Goal, users and boundary

**Primary-user hypothesis:** an operations or procurement lead at a small B2B software/services business, preparing a first review of an English-language services agreement for a qualified legal reviewer. Their job is to identify questions, preserve evidence and organize negotiation decisions. Validate this hypothesis through 6–8 interviews and observed synthetic-document reviews, including at least two keyboard/screen-reader users and two qualified contract reviewers. Do not infer the applicable jurisdiction from the developer's location.

**Pilot-scope hypothesis:** one organization, 5–15 invited reviewers, English digitally generated services agreements, up to 50 pages and 10 MiB per file. The initial scope excludes autonomous legal opinions, signing approval, sending revisions to counterparties, automatic replacement of original wording and legal research. Broader contract types, languages, scanned files and 200-page documents are separately gated capabilities. Unsupported documents may be stored only if policy allows; they must not receive a reassuring analysis.

The assistant spots possible issues in supplied evidence. A human must confirm source accuracy, context and any revision before using it. The app must not label a contract safe, legally compliant, enforceable, or ready to sign. Legal conclusions and jurisdiction-specific recommendations require qualified review outside automated issue spotting. Human acceptance of a finding means agreement with that observation, not permission to sign.

## Information architecture

| Area | Main contents | Persistent identity |
|---|---|---|
| Document library | Search, review status, processing failures, versions, owner, retention date | Workspace/document ID |
| New review | File selection, context, privacy, validation | Draft review ID |
| Processing | Actual stage, extraction coverage, warnings, retry/cancel/resume | Job ID |
| Review | Original/extracted text, findings, finding detail, questions, review notes | Review version + finding/span IDs |
| Compare | Baseline/current versions, aligned clauses, substantive change list | Comparison + two version IDs |
| Export & data controls | Snapshot choices, provenance, retention, deletion progress | Export/deletion receipt ID |

Use stable routes and deep links to findings and source spans. Back navigation preserves filters, selected finding, source page, scroll position and unfinished edits. A denied/deleted deep link reveals no filename or document metadata. The library is a work queue, not a decorative score dashboard.

## Review context

Before analysis, collect contract type; represented party by exact named entity and role (customer/provider/other); known governing law and forum as separate fields; objectives (payment, liability, IP, termination, data handling, other); and optional playbook/version. Each supports “unknown / needs confirmation.” Record whether a value is user-confirmed, extracted or inferred. Suggestions quote their supporting text and are editable. Jurisdiction is never auto-confirmed. Warn on conflict between chosen context and document text.

Unknown context allows extraction and neutral evidence questions. Context-dependent findings explain what is missing and withhold a definitive assessment. Changing context creates a new analysis version and marks previous decisions for re-review, without overwriting them. Avoid collecting unnecessary sensitive business details; provide explicit permission controls for custom notes.

## Journeys and acceptance criteria

### 1. Start or return to a review

An empty library explains supported scope and offers a labelled synthetic example plus “Upload for review.” A populated library shows document/version, last updated, assigned reviewer, processing state, coverage warning and decisions remaining. Search/loading/error/no-results are distinct. Library failure has retry; no-results has clear filters. Open review restores saved state after refresh. Duplicate filenames are permitted with distinct version labels.

### 2. Upload deliberately

Selecting a file does not immediately transmit it. Show filename, size, supported PDF/DOCX/TXT scope, 10 MiB pilot limit, review context and exact privacy policy before “Start processing.” File browsing is always available. Explain scanned/encrypted/unsupported formats and replacement options. Proposed privacy copy must be populated from approved deployment policy: who can access, provider recipients, processing region, retention duration, provider retention exceptions and deletion/backups. If unknown, block confidential upload; never claim “private,” “not used for training” or instant deletion without verification.

Progress distinguishes bytes transferred from processing. Hash after bounded streaming; detect same bytes within the authorized workspace. Offer “Open existing review” or “Create new context/version”; do not reveal cross-workspace duplicates. Concurrent duplicate requests with same idempotency key resolve to one job. Context form errors link from a summary to the first invalid field, preserve input and do not rely on color.

### 3. Process and recover

Stages: upload → security checks → text extraction → source verification → issue spotting → evidence validation → ready/partial/failed. Display real completed units where measurable; do not invent percentage or ETA. Show elapsed time and stage, plus a safe resume link. Timeout of a browser request is not job failure. Navigating away must not cancel a committed job.

| State | Message/action |
|---|---|
| File signature/format rejection | Explain allowed format; replace file; nothing sent to AI |
| Scan needs OCR | Identify affected pages; use text-based copy or explicitly opt into available OCR; no silent success |
| Password protection | Ask for an unlocked copy; do not retain passwords |
| Malformed/oversize/too many pages | Explain limit and safe replacement route; no parser stack trace |
| Provider timeout or rate limit | Keep completed stages; retry within budget or show resume action |
| Partial extraction | List readable/unreadable pages; original available for manual review; suppress absence claims |
| Cancellation | Stop scheduling; show cancelling until worker acknowledges; offer deletion separately |
| Worker loss | Recover from durable job lease; retain job identity; do not demand re-upload |

Error focus goes to a heading after a user action; background updates use polite status announcements without moving focus. Retry buttons say which stage restarts and whether extra provider cost is possible.

### 4. Review evidence and decide

Desktop has a document pane, findings list and finding detail. The source pane shows original page with highlight and a synchronized accessible text view. DOCX uses a clearly labelled rendered view tied to block IDs; generated page numbers are not represented as original source pagination. Text view has headings and table structure. Long originals load pages on demand; finding rows are paginated or accessibly virtualized.

Each finding contains a stable ID, issue type, exact quoted span(s), page/section/block location, explanation of consequence, affected party, relevant user objective, uncertainties, proposed action, AI generation version and human decision history. A contradiction requires two spans and a clear account of why they conflict; show possible reconciliation and exceptions. A missing-clause observation says “Not located in the reviewed material,” with reviewed scope and expected playbook requirement; do not fabricate a source span for an absence.

| Separate dimension | Proposed values | Meaning |
|---|---|---|
| Potential impact | High / Medium / Low / Not assessed | Consequence if the described condition applies, with rationale |
| Evidence status | Supported / Needs verification / Insufficient evidence | Whether text and context support the observation; not an invented probability |
| Business preference | Required by playbook / Negotiable / No preference / Unknown | Organization's policy or choice, attributed to its source/version |
| Human decision | Unreviewed / Accepted observation / Dismissed / Edited / Escalated | Explicit reviewer action, author and time |

“View evidence” focuses the destination text/page heading and highlights a bounded span. “Back to finding” returns to the initiating control; next/previous findings have native controls. Text-only users get the same quotes and relationships. No finding is considered reviewed just because it entered the viewport.

Accept records agreement with the observation; dismiss records a reason; edit preserves generated text and revision diff; annotate adds a versioned note; escalate records unresolved context. Save feedback includes pending/saved/failed and retry. Use revision numbers/ETags to detect competing edits; a conflict preserves both drafts. Suggested clause text is a draft, with assumptions and possible tradeoffs. It never silently changes the original. A reviewer may export unresolved work, but it is clearly labelled incomplete.

### 5. Ask bounded questions

Questions are scoped to the selected version and confirmed context. Each factual assertion links to one or more exact verified source spans. Answers distinguish quotation, interpretation and unresolved context. “Is this safe to sign?” prompts human review rather than a yes/no conclusion. Empty retrieval yields “I could not locate support in the reviewed text.” Partial extraction says which pages were not available. Vector failure yields a technical retry state, not an absence claim. Question length is bounded and the draft survives network errors. Show sources inline; never auto-open links found in a document.

### 6. Compare substance

Require baseline and revised versions, consistent party/context, and ready extraction. Align all clauses including repeated types; support split/merged clauses, moves and uncertain matches. Provide manual realignment. Display both exact texts, additions/removals and changes to actor, duty, amount, deadline, scope, exceptions, definitions and cross-references. Separate cosmetic changes from potentially substantive ones; retain cosmetic changes in a filter. An identical score never establishes identical meaning.

Describe consequence from the selected party's objectives with evidence from both versions; no overall winner. A missing counterpart can be “unmatched” until coverage and alignment are confirmed. On mobile, stack baseline and revision with persistent version labels; provide “jump to paired clause” and return focus. Independent scrolling is default; synchronized scrolling is optional and cannot hide the matched location.

### 7. Export and delete

Export preview lists selected findings, dismissed findings inclusion, unresolved items, notes and whether original quotations are included. Include document hash/version, context, coverage, run versions, reviewer actions, timestamps and issue-spotting disclaimer. Default is an accessible HTML review record; PDF is optional and must be tested. No automatic email/share or counterparty submission. Export failure preserves choices and supports retry.

Deletion requires a plain summary of the exact document/version and dependent analyses, chunks, questions, comparison results, notes and generated exports. The user can cancel before confirming. Reauthentication is required when policy/session age demands it. On confirmation, revoke access immediately, show purge progress and a receipt; show backup/provider exceptions and outside-app downloaded copies. A failed store purge remains visible as pending action and alerts operations. Deleting one operand invalidates/purges comparisons containing its text. Removing a library row is not deletion.

## Responsive and accessibility requirements

Use semantic headings, native controls, visible focus, skip links and logical order. Under 900 px the three panes stack; under 600 px actions wrap and finding selection/detail/evidence use anchor-linked sections with return links. At 320 CSS px/400% zoom no page-wide horizontal scroll is acceptable except inherently two-dimensional source tables with an accessible alternate view. Touch controls target 44×44 CSS px as a product goal. Reduced motion disables nonessential transitions. Preserve text labels alongside severity colors.

Target WCAG 2.2 AA; verify keyboard access, focus visibility/order/obscuring, labels, status messages, contrast, reflow and error recovery. This target is not a conformance claim. [WCAG 2.2](https://www.w3.org/TR/WCAG22/) and [WAI dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) guide testing. Dialogs require initial focus, contained Tab order, Escape and focus return; prefer inline detail panes where a modal is unnecessary.

## Priorities and measures

P0: trust and access boundaries, bounded ingestion, source fidelity, explicit failures, deletion, accessible review decisions and offline evaluation. P1: substantive comparison, complete export, production performance tuning and broader scanned-document support. P2: approved additional contract types/languages, richer team playbooks and collaboration. No feature may bypass its P0 gate.

All targets below are proposed pilot gates, not current measurements. Segment by contract type, page count, parser/OCR mode, context completeness and version. Log IDs/counts/timings, not contract text.

| Metric | Definition / initial target |
|---|---|
| Review completion | Reviews explicitly completed after every presented finding is dispositioned or explicitly deferred / eligible started reviews, measured at 7 days; baseline first, seek ≥80% in moderated pilot |
| Correction rate | AI observations materially edited or dismissed as wrong / adjudicated AI observations; report preference-only dismissals separately; target downward trend, never optimize by hiding findings |
| Evidence accuracy | Correct, supporting source-span links / adjudicated links; proposed ≥99% and zero cross-document citations |
| Processing time | Commit-upload→ready/partial, p50/p95 by 1–10, 11–50 and later 51–200 pages; proposed p95 ≤120 s for digital ≤10-page pilot files under stated load |
| Accessibility | Completion of upload→evidence→decision→export/deletion using keyboard and screen reader; 100% critical journey completion, zero unresolved critical blockers |
| Cost/document | Metered parsing/OCR, embedding, inference including retries, allocated processing/storage/export cost / attempted documents; report failures separately; pilot budget proposed ≤€0.50 median and ≤€2 p95 for ≤10-page digital files, to validate against selected providers |
| Reviewer usefulness | Blinded 1–5 usefulness plus time-to-verified-decision compared with manual baseline; target median ≥4 without increased missed important issues |
| Reliability | Completion, partial and terminal failure rates as separate numerators; retry/cancel effectiveness and deletion time; never count partial as fully analyzed |

Telemetry events: upload_committed, stage_changed, coverage_confirmed, evidence_opened, decision_saved, review_completed, export_created, deletion_requested/completed. Use authorized pseudonymous IDs, version and coarse duration buckets; no filenames/questions/quotes in analytics. No session replay on document screens. Product lead owns usefulness/completion; AI lead owns adjudicated quality; engineering owns latency/cost; security owns isolation/deletion; accessibility reviewer owns critical journeys.
