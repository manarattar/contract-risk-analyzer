> 2026-09-11 update: [suggested revision drafts are deployed and verified](revision-drafts-release.md). Suggestions remain unapproved and separate from the source contract.

> Current release (2026-09-10): the public experimental AI trial is live. See [verified capabilities and limits](public-ai-trial-release.md). The audit and qualified-production roadmap are not a claim that every production gate is complete.

> Latest deployed status (2026-09-10): public registration and private sandboxed manual uploads are live. See [public access release](public-access-release.md). Live AI remains pending; earlier audit findings describe the original baseline.

# Contract-review assistant: production-readiness audit

Audit date: 9 September 2026. Original scope: audit and planning only. The user subsequently authorized implementation. The assessment below describes the original baseline, not the replacement v2 implementation. See [implementation status](implementation-status.md) and [operations](operations.md) for current behavior and remaining release gates. Historical file/line references refer to the audited baseline and may have shifted.

## Executive assessment

**Keep this implementation at synthetic-demo readiness. Do not admit confidential pilot documents until the P0 gates below pass.** The repository implements upload, parsing, analysis, Q&A, score-based comparison and PDF export. It does not implement authenticated document ownership, durable processing, a source-linked review workspace, review decisions, document history or full deletion. Some outputs are fixed mock data; live Q&A also falls back to canned assertions when retrieval returns nothing. Failed clause analysis can appear as low risk.

These are code findings, not a claim that the deployed service was penetrated or that every live result is mocked. No live site, provider, production database, uploaded contract or confidential example was accessed. No legal accuracy or regulatory compliance is asserted.

## Repository and preservation

- Verified repository: `E:\Manar\claude_projects\contract-risk-analyzer` (the requested `E:\Manar\claude\_projects` does not exist).
- Identity: Git root, README product name and matching FastAPI/React workflow. Reviewed HEAD: `6bbcd0e8af6deff14e5a6d97b4da23e21fb6861e`.
- Existing modification: `.gitignore`; preserved. SHA-256: `701534A41E4C0C8A23EE4B809968BA6F56930382F477B12400999D26AEA4CDB1`.
- No AGENTS.md found in the repository (including hidden paths outside dependency/Git directories) or checked ancestors `E:\`, `E:\Manar`, `E:\Manar\claude_projects`.
- Application code, dependencies, deployment and databases were not changed. Deliverables are confined to this directory. Existing data, `.env` values and contract files were not read.

## Read these deliverables

| Deliverable | Purpose |
|---|---|
| [audit.md](audit.md) | Confirmed findings, code evidence, workflow trace and limitations |
| [product-spec.md](product-spec.md) | Proposed users, review behavior, information architecture and metrics |
| [architecture.md](architecture.md) | Proposed data model, ingestion, AI boundaries, threat model and deletion |
| [implementation-backlog.md](implementation-backlog.md) | P0/P1/P2 work, dependencies, estimates, acceptance tests and release gates |
| [evaluation-and-test-plan.md](evaluation-and-test-plan.md) | Evaluation corpus, measurement definitions, test matrix and recorded checks |
| [wireframes/index.html](wireframes/index.html) | Six dependency-free, responsive HTML/CSS concept screens; synthetic examples only |
| [sources.md](sources.md) | Primary standards and technical sources, accessed date and applicability |

Open the wireframe HTML directly in a browser. Navigation and disclosure controls work locally; upload, saving, export and deletion are annotated concepts and do not call an API. All wireframe privacy and service-level values are proposed policies, not descriptions of the current service.

## Ten most important actions

1. **B01:** Make demo provenance unmistakable; remove canned live Q&A fallback and low-risk failure defaults.
2. **B02:** Require authentication and owner/workspace authorization on every document operation and comparison operand.
3. **B03:** Bound ingestion before full buffering; quarantine, validate signatures and isolate parsers.
4. **B04:** Preserve page/block/character evidence and detect unreadable or incomplete extraction.
5. **B05:** Replace process-local tasks with durable jobs, independent sessions, idempotency and recovery.
6. **B06:** Validate every finding and answer against source spans; abstain and expose partial coverage.
7. **B07:** Establish retention, provider handling and deletion across all copies and backups.
8. **B08:** Replace scores and signing recommendations with an accessible evidence-first workspace and recorded human decisions.
9. **B09:** Establish a reviewer-adjudicated held-out evaluation corpus and release thresholds.
10. **B10:** Make CI, dependency review, deployment configuration, monitoring and restore drills release gates.

See the backlog for exact dependencies: this list is a priority summary, not a claim that all work can run sequentially or within ten small changes.
