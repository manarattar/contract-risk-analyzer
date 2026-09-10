# Public experimental AI trial — 2026-09-10

Live URL: https://contracts.manarattar.com/
Release: `review-20260910-110149`.

Anyone can create an account. Uploaded documents stay scoped to that account. The public synthetic demo remains available without registration and never calls an AI provider.

## Verified working

- Registration, private sign-in, logout and revocable sessions.
- PDF and UTF-8 TXT upload through the real public API, isolated extraction and durable processing. DOCX parsing remains covered by offline tests rather than this live smoke run.
- Real OpenAI issue spotting with schema-constrained findings, exact supporting quotes, uncertainty and suggested actions.
- Original PDF pages and source navigation; reviewer decisions, annotations and editable revision drafts.
- AI answers with verified source spans; unsupported answers are rejected or abstained.
- Two-document candidate comparison, authenticated HTML export, immediate access revocation and completed active-store purge.
- Desktop/mobile registration checks and the public demo regression.

Evidence: `evidence/public-ai-trial-live.json`, `evidence/demo-after-ai-release.json`, `evidence/public-signup-live-browser.json`, `evidence/ai-pdf-job-stage.json`. Offline release checks: **91 passed, 13 integration tests deselected**, one upstream deprecation warning; frontend lint/build passed.

## Trial limits and honest boundaries

Five active documents per account, 500 globally; 10 MiB and 50 PDF pages; supported review context is services agreements. Active retention is 24 hours. Encrypted on-server backups last up to 14 days; deletion records must be replayed before recovery. No off-site recovery or external alert channel is established.

Model: `gpt-4.1-mini-2025-04-14`, prompt `evidence-only-2`. The application reserves $0.10 before every AI attempt and stops when the UTC-day reservation reaches $5. Reservations include failed attempts and overestimate the bounded requests; they are not a statement of billed cost. The cap covers this application, not other uses of the shared provider account. Each document also has a 20-attempt limit. Staging checks used separately bounded synthetic-only temporary stores.

Provider requests use Chat Completions with `store=false`. Default abuse monitoring can retain content up to 30 days; no account-specific zero-retention or regional guarantee has been verified. The upload screen discloses provider handling and requires acknowledgement. Use non-confidential trial documents. Application deletion cannot erase provider logs or downloaded copies.

This is explicitly **experimental**, not the qualified-production `live` mode. The existing qualified-review evaluation gate remains intact for that mode; no reviewers, legal metrics or approvals were fabricated. Quote matching verifies the source span, not the legal correctness or semantic support of every interpretation. Independent legal/security/accessibility review and a held-out adjudicated corpus remain outstanding.

Scanned-document OCR, verified substantive clause alignment, automatic contract redlining, accessible PDF export, team document sharing and self-service account recovery are not completed features. Comparison currently shows text-based candidate alignments with possible amount/timing/duty changes; it must not be advertised as a qualified legal comparison. Suggested actions and human-editable drafts do not imply automatic legally suitable replacement wording.

## Validation failure and correction

An initial real-provider staging request failed validation; a repeated request passed. The first live PDF run also failed safely and exposed no unverified findings. AI was switched back to manual mode. The revised pipeline added schema-constrained findings, clearer prompt constraints, safe diagnostic codes and unique whitespace-equivalent quote mapping back to original text/offsets. The exact first failure was not established by the generic earlier error. The revised full PDF staging job and live PDF/TXT flows passed. These small checks establish functioning plumbing, not statistically reliable legal accuracy.

## Deployment and rollback

Account and budget tables were explicitly initialized before enabling their features. The trusted worker now has a separate provider-egress Docker network; parser subprocesses still cannot create sockets and receive no provider credentials. `deployment/compose-ai.yml` records the network topology. Runtime keys live only in protected server configuration, never in this repository.

To pause AI, set `REVIEW_MODE=manual` in the protected environment and recreate API and worker using the current release compose file. Existing source material stays reviewable; new uploads receive no AI findings. Keep the retention/deletion worker running. Previous environment and hostname blocks are retained in root-protected release files. Restoring an older database must preserve the current deletion ledger and conservatively preserve the day's AI budget reservations.

Sources checked 2026-09-10: [OpenAI model pricing and supported features](https://developers.openai.com/api/docs/models/gpt-4.1-mini), [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data), [Linux Landlock](https://docs.kernel.org/userspace-api/landlock.html).
