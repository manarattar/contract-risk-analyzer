# Suggested revision drafts — 2026-09-11

Revision drafts are separate from contract text, source quotes, and reviewer-authored drafts. Findings may contain `suggested_revision` and `revision_caveats`; existing records without these fields remain readable. A proposed draft without caveats is rejected. Signing/enforceability assurance checks also apply to draft text and caveats.

The prompt is version `evidence-only-3`. Drafts are illustrative and may contain explicit placeholders for unspecified negotiated terms. When context is insufficient, the model can omit a draft. No replacement is applied to the source contract. This is not automatic redlining or a finding that proposed wording is legally suitable.

The review workspace exposes the suggested wording and caveats, then lets a reviewer copy it into their editable draft. Copy is disabled when a current draft contains text. Copying moves focus to the editor and selects the edited decision state; a reviewer note and explicit save remain required. Existing decision conflict/version checks apply. Export distinguishes unapproved suggested wording from the saved reviewer draft and escapes both as text.

Verification before release: 93 offline Linux tests passed, 13 live integration tests excluded, one upstream deprecation warning; frontend lint/build passed. Browser checks at 1440x1000 and 375x900 passed for copy, focus, overwrite protection, saved decision and overflow. A separately bounded synthetic provider check produced two findings and two revision drafts with caveats and exact source quotes; this is an engineering check, not qualified legal evaluation.

Evidence: `evidence/revision-draft-browser.json`, desktop/mobile screenshots, `evidence/revision-ai-stage.json`. Tests: `backend/tests/test_revision_drafts.py` covers caveats, prohibited assurances, source preservation and export escaping.

The public trial's privacy, retention, budget, source-verification and human-review limitations continue to apply. No database migration or confidential contract was used for this change.


Deployed and verified: `review-20260911-141637`, code commit `3c54bb5e52168026b45547393190650ca980164a`. Hosted CI passed: https://github.com/manarattar/contract-risk-analyzer/actions/runs/34609320870. Live browser checks and PDF/TXT AI upload, questions, comparison, export, deletion and purge passed; see `evidence/revision-draft-live-browser.json` and `evidence/revision-public-ai-live.json`. Worker health was good with zero pending purges at verification.
