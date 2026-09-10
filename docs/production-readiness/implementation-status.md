# Implementation status — updated 10 September 2026

**Release update:** v2 is deployed at https://contracts.manarattar.com/ with a public, isolated, expiring synthetic PDF demo and private sign-in. Original PDF page rendering, quote/block overlays and keyboard evidence navigation are implemented. The full Linux suite passed 77 tests, with 13 provider tests excluded. Live API and desktop/mobile browser checks passed. See [deployment record](deployment/README.md). Earlier paragraphs below describe the pre-deployment foundation; qualified review, untrusted-file isolation, managed identity and recovery gates remain open.

The subsequent instruction to execute the plan authorized application changes. A separate v2 review service and interface now replace the served legacy application. This is a synthetic-demo release candidate, not an approved confidential-document pilot. No deployment, paid model call, production migration, confidential contract or existing document database was used. The existing root `.gitignore` change is preserved.

## What is implemented

- Versioned `/api/v2` routes with hashed bearer credentials, strict document owner/workspace checks, roles, bounded requests and quotas. Legacy unauthenticated routes are not mounted. Tokens stay in browser memory.
- Explicit disabled, demo, manual and live modes. Demo observations belong only to a fixed synthetic sample; failures never become reassuring risk results. Upload and live provider gates default closed.
- Separate explicitly initialized SQLite store; durable leased jobs, checkpoints, retry/cancel guards, idempotent creation, retention and deletion receipts. Existing legacy records are not silently assigned ownership or migrated.
- Bounded upload and parser subprocess boundaries, safe generated storage names, PDF/DOCX signatures, DOCX archive checks, page/character limits and partial coverage warnings. Source blocks preserve exact quote offsets and PDF page/bounds where available.
- Strict generated-output validation, provenance and evaluation-manifest gating. Source Q&A returns matching document passages or abstains; it does not manufacture legal answers. No v2 vector index is created.
- Context capture, paginated document library, processing/recovery, responsive evidence workspace, quote navigation, reviewer decisions and annotations, completion acknowledgement, escaped HTML export and deletion controls.
- Comparison exposes aligned change candidates and wording hints, requiring human interpretation. It makes no substantive-equivalence or preferred-contract assertion.
- CI definition, isolated locked dependency setup, nonroot container configuration and operations guidance. These configurations have not been deployed.

## Backlog disposition

“Partial” means useful implementation exists but the original package's complete acceptance criteria have not been demonstrated.

| Package | Status | Remaining work before its full acceptance |
|---|---|---|
| B01 trustworthy states | Implemented locally | Revalidate every real provider failure in a qualified environment. |
| B02 identity/ownership | Partial | Managed identity/SSO, credential lifecycle and revocation UX, approved workspace membership and independent authorization review. Static configured credentials are a local bootstrap mechanism. |
| B03 ingestion | Partial; uploads gated | Prove Linux isolation and resource limits, network denial, malware policy/scanning and hostile-parser testing. A subprocess alone is not a security sandbox. |
| B04 extraction | Partial | Original-document page rendering, multi-column/table relationship evaluation, missing-page adjudication and layout corpus. Extracted blocks are not a faithful facsimile. |
| B05 jobs | Implemented locally; operational proof pending | Multi-worker stress, crash/lease recovery under production load and operational cancellation/billing behavior. No exactly-once provider billing promise. |
| B06 grounded AI | Partial; live gated | Qualified live evaluation, contradiction/missing-clause reasoning, retrieval relevance beyond lexical source search and safe revision quality. |
| B07 retention/deletion | Partial | Approved retention/provider agreements, backup expiry and restore suppression drills. Receipt confirms active logical store/file processing, not forensic erasure of WAL, backups, provider copies or downloaded exports. |
| B08 human review | Partial | Original page view, assistive-technology testing, qualified usability study and richer history. Current decisions use optimistic conflict protection. |
| B09 evaluation | Harness/gate only | Real labelled, adjudicated and held-out corpus; confidence intervals and all quality slices. Candidate manifest intentionally fails eligibility. No legal quality score is claimed. |
| B10 operations | Partial | Run hosted CI, Linux container verification, image digest/action pinning policy, monitoring integration, incident exercise, migrations for future schema changes and restore drill. |
| B11 comparison | Partial | Human-adjudicated substantive alignment, moved/merged clauses and cross-reference effects. Current textual candidates are explicitly limited. |
| B12 exports | Partial | Accessible PDF/DOCX, download browser verification and export accessibility review. Current artifact is escaped provenance-bearing HTML. |
| B13 tuning | Partial | Representative load tests, field performance, measured processing/cost percentiles and cost ledger. Current quotas are guardrails, not measured cost. |
| B14 OCR | Not implemented | Keep scanned/unreadable pages partial; no silent OCR inference. |
| B15 expansion | Not implemented | Approved contract/language/playbook scope and held-out evaluation for each expansion. |
| B16 collaboration | Not implemented | Assignments, membership/sharing policy and multi-reviewer workflows. Strict individual ownership currently applies. |

## Verification and evidence limits

Local results: 61 backend tests passed; the later evaluation-gate regression run passed 7 tests (6 newly added). Frontend lint/build and refreshed-runtime desktop/mobile browser walkthrough passed. Frontend all-dependency and backend runtime-lock audits reported zero known vulnerabilities. See the verification log for exclusions and the upstream deprecation warning.

The automated backend suite exercises synthetic documents only: cross-owner access, input gates, source spans, decisions/conflicts, escaping, lease recovery, cancellation, deletion, malformed extraction and abstention. Legacy provider integration tests are excluded; no paid request was made. See `evidence/verification.txt` for final commands/results and dependency audit snapshots.

`evidence/browser-check.json` records a local Edge/CDP walkthrough and desktop/mobile screenshots. The walkthrough covers login, library, synthetic processing, evidence focus, decisions, source Q&A, annotations and deletion; it is not a screen-reader certification. No horizontal overflow was observed at 375 px in checked screens. Screen-reader behavior, all WCAG criteria, Linux sandbox operation, hosted CI, real provider behavior, realistic long-document performance, restore procedures and legal accuracy remain unverified.

## Release decision and next ten actions

1. Keep the release on synthetic demo data with uploads/live AI closed.
2. Complete managed identity and credential revocation before admitting a pilot tenant.
3. Prove parser isolation, quotas and malware controls against hostile synthetic fixtures.
4. Validate original-document rendering, layout fidelity and extraction coverage.
5. Build and adjudicate the held-out evaluation corpus with qualified reviewers.
6. Pass citation, unsupported-claim, precision/recall and critical-error gates before live AI.
7. Approve provider handling, retention and backup deletion; conduct a restore/deletion drill.
8. Run independent authorization, accessibility and human-review usability checks.
9. Validate Linux deployment, monitoring, incident recovery, concurrency and cost limits.
10. Run a narrowly scoped supervised pilot; defer semantic comparison, OCR and expansion until their own gates pass.

The original implementation backlog remains the source for dependencies, effort ranges and full acceptance criteria. Do not mark all B01–B16 complete based on the local implementation.
