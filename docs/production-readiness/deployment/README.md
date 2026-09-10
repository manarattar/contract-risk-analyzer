# Verified release: 10 September 2026

The v2 application is live at https://contracts.manarattar.com/. Release directory: `/srv/apps/contracts-v2/releases/review-20260909-234114`; frontend: `/srv/www/contracts-v2/review-20260909-234114`. Backend and worker containers are `contracts-v2` and `contracts-v2-worker`. The new named volume is `contracts_review_v2_data`. No legacy records or volumes were migrated or removed.

The public demo creates a random signed identity valid for 30 minutes, isolated synthetic review records, and a generated two-page PDF. Public identities cannot upload or access private records. A worker expires and purges demo documents. The private owner credential is stored only in the protected server file `/srv/stack/env/contracts-v2-owner-token`; runtime configuration is `/srv/stack/env/contracts-v2.env`. Credentials are not included in this repository. Managed sign-in and reviewer onboarding remain separate work.

The live mode is manual with uploads disabled and no provider configured. Server-generated synthetic PDF pages are available without enabling untrusted-file rendering. Private PDF rendering requires `REVIEW_PAGE_RENDERING_ENABLED` and approved isolation. DOCX/TXT remain text-only; OCR is not implemented. No qualified legal accuracy or compliance is claimed.

## Verification

- 77 tests passed in a Linux container with no network, read-only root, nonroot user, dropped capabilities and memory/process limits; 13 provider integration tests excluded. One upstream Starlette/AnyIO deprecation warning remains.
- Frontend lint/build passed; generated asset bundle contains no development API address.
- Staging smoke and HTTPS live smoke passed: ownership isolation, synthetic PDF processing, exact quote highlight, source Q&A, review decision, escaped HTML export, deletion denial and purge receipt.
- Live desktop (1440×1000) and mobile (375×900) browser walkthrough passed with no recorded runtime exceptions: quote highlight/focus, page navigation, return focus, text alternative and no horizontal document overflow. Mobile controls were widened after screenshot review.
- Caddy validated and reloaded only the `contracts.manarattar.com` block. API and page responses use no-store; CSP and upload-size limits apply. TLS is handled by the existing Caddy service.
- Evidence: `../evidence/live-smoke.json`, `../evidence/live-viewer-browser.json`, and `../evidence/live-viewer-*.png`. Synthetic processing took 3.34 seconds in this one live smoke run; this is not a performance percentile or SLA.

## Rollback and maintenance

`previous-host-block.Caddyfile` in the release directory preserves the prior hostname block. The legacy `contracts` container and `/srv/www/contracts` remain untouched. A rollback to that legacy application restores its old security limitations, so prefer fixing/rolling back within v2 or temporarily disabling access for a security incident. Do not reopen legacy unauthenticated routes as a routine security rollback.

For another v2 release: build in a fresh release directory, initialize only the explicitly selected v2 schema, run the restricted test container and synthetic staging smoke, publish versioned frontend assets, validate the target hostname block, then reload Caddy. `prepare.sh`, `Dockerfile.test`, `compose.yml`, `switch.py`, and `smoke.py` document the executed workflow. Review the shared Caddy file before each change; do not overwrite unrelated hostnames.

The bootstrap demo identity rate limit intentionally sees the reverse-proxy peer because the API does not trust forwarded headers. This limits all visitors sharing that peer to five new demo sessions per minute. Any change to client-IP handling must configure a trusted proxy boundary first.

Still required: independent accessibility/security review, managed identity, qualified AI adjudication, private-file isolation, complete retention/backup/restore validation, and measured load/cost testing. The live public demo is not evidence that these gates passed.
