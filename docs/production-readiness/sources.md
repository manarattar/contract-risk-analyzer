# Sources and evidence register

Implementation dependency follow-up (9 September 2026): checked the primary [python-multipart security advisories](https://github.com/Kludex/python-multipart/security/advisories), including [GHSA-59g5-xgcq-4qw3](https://github.com/advisories/GHSA-59g5-xgcq-4qw3) and [GHSA-pp6c-gr5w-3c5g](https://github.com/advisories/GHSA-pp6c-gr5w-3c5g). Versions were resolved from official PyPI/npm metadata. Audit outputs under `evidence/` are point-in-time dependency checks, not proof of application security.

Accessed 9 September 2026. Primary sources only. Guidance informs recommendations; none establishes this application's compliance, legal correctness or deployed controls. Product-specific thresholds, architecture decisions and policies are explicitly proposals.

| ID | Source / current observed edition | Applied to |
|---|---|---|
| S01 | [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/), Recommendation dated 12 December 2024 on accessed page | Proposed AA target; keyboard, contrast, reflow, focus, labels and status/error testing |
| S02 | [WAI-ARIA Authoring Practices: modal dialog](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) | Dialog keyboard interaction, initial/contained/return focus and dismissal; not a substitute for testing |
| S03 | [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), living guidance | Layered validation, safe names/storage, limits, scanning and parsing boundary |
| S04 | [OWASP Application Security Verification Standard](https://owasp.org/www-project-application-security-verification-standard/), project page | Pin a release and select verification requirements for authentication, authorization, file handling and deployment during implementation |
| S05 | [OWASP LLM Prompt Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html), living guidance | Separate untrusted content, least privilege, output validation and adversarial testing |
| S06 | [Core Web Vitals](https://web.dev/articles/vitals), Google web.dev | LCP/INP/CLS and p75 field targets; distinguish page experience from job latency |
| S07 | [NIST AI 600-1: Generative Artificial Intelligence Profile](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf), July 2024 | Lifecycle risk tracking, evaluation and human oversight; no certification implied |
| S08 | [SQLAlchemy 2.0: Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html) | Explicit session/transaction lifetimes and rollback/close design |

These pages were opened using web access during the audit. No confidential source text or repository contents were sent to web search. No provider-specific retention guarantee or specific dependency vulnerability is asserted. The actual OpenAI-compatible provider endpoint, terms, processing region and account controls remain unverified; select primary provider documentation and contractual evidence before pilot approval.

## Local evidence

Verified repository: `E:\Manar\claude_projects\contract-risk-analyzer`; HEAD `6bbcd0e8af6deff14e5a6d97b4da23e21fb6861e`. [audit.md](audit.md) supplies line-level references. Source categories inspected:

- Backend entry/config/data/schemas: `backend/app/main.py`, `config.py`, `database.py`, `schemas.py`.
- All five router modules: upload, analysis, QA, comparison, report.
- Parser, splitter, analyzer/prompts, vector store, mock analysis, comparison and report services.
- React App/API and upload, compare, dashboard, clause detail/table, chat, disclaimer and report controls; CSS, package and lint configuration.
- Existing calibration tests, dependency declarations/lockfile presence, Dockerfiles, compose, nginx and deployment documentation.
- Git inventory/status and AGENTS.md search; safe checks recorded in [evaluation-and-test-plan.md](evaluation-and-test-plan.md).

The deployment guide is a local claim, not authoritative evidence of current infrastructure. Its Postgres/database-environment and committed-venv statements do not match the inspected source/inventory: code hardcodes SQLite and `git ls-files '*venv*'` returned no entries. Existing venv/data/Chroma directories exist locally but were not treated as source evidence about confidential content or production.

## Evidence limitations and maintenance

Line numbers can drift after future edits; retain this baseline commit alongside findings. No `.env` values, stored DB/vector contents or existing contracts were inspected. Source absence means absent in the searched repository, not absent from an external host or private infrastructure repository. No production network, authentication, provider or backup tests were run.

Recheck living sources and selected ASVS release when implementing. Keep a dated control-to-test matrix and revise the audit after P0 work. Qualified legal, security and accessibility reviewers must approve their scoped decisions; this planning package does not replace them.
