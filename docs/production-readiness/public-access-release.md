# Public access release — 2026-09-10

Deployed release: `review-20260910-104054` at https://contracts.manarattar.com/.

Anyone can register a private account without an invitation. Each account receives a distinct server-generated workspace; owner-only account administration remains scoped. Passwords use scrypt N=131072/r=8/p=1; opaque sessions expire after eight hours or 30 minutes idle. Logout/revocation invalidate stored session hashes. Recovery invitations suspend old credentials immediately. Public self-service accounts currently have no automated recovery; save credentials.

Uploads are enabled in **manual mode** for non-confidential trial documents: PDF, DOCX and UTF-8 TXT, at most 10 MiB/50 pages, five active documents per account, 500 globally. Records expire after 24 hours. Scanned PDFs without readable text are not supported. No legal quality approval or regulatory compliance is claimed.

Parser and page-renderer subprocesses receive a sanitized environment. On this x86_64 Linux host (Landlock ABI 4), read access is limited to runtime/application code and one document. Filesystem mutation, sockets, process creation, execution and selected process-interference calls are denied using Landlock and seccomp. Controls fail closed if unsupported. This is a tested containment layer, not an independent security certification.

Verification: 88 offline Linux tests passed, 13 integration tests excluded, one upstream deprecation warning. Frontend lint/build passed. Desktop 1440x1000 and mobile 375x900 registration/login/logout checks passed locally and live with no captured JavaScript exceptions or horizontal overflow. Live synthetic PDF/TXT upload, processing, source questions, comparison, export, foreign-account denial, deletion and purge passed. Public demo regression passed. See evidence/public-trial-live.json, public-demo-after-signup.json, public-signup-live-browser.json and matching screenshots.

The deployment explicitly initialized additive account tables before enabling accounts. Existing document tables and legacy deployment were preserved. Previous environment and hostname configuration are retained server-side for rollback; those files contain secrets and are not copied into this repository. Session/invitation tables are excluded from backup snapshots. Encrypted on-host backup retention remains 14 days; no off-host recovery or external alert delivery is established.

Live AI is the next release: the local Cerebras configuration returned HTTP 403 on metadata access. The older project deployment's OpenAI configuration passed an authenticated model-list request; credentials were neither printed nor copied to source control. No inference calls were made for this release. Qualified legal evaluation, OCR, provider-backed answers and substantive comparison remain separate pending capabilities.

Primary sources: [Linux Landlock documentation](https://docs.kernel.org/userspace-api/landlock.html), [seccomp manual](https://man7.org/linux/man-pages/man2/seccomp.2.html), [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html). Accessed 2026-09-10.
