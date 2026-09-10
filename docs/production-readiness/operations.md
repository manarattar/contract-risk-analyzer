# v2 operating notes

This describes the implemented local release candidate, not a deployed or approved pilot. See `implementation-status.md` for gate status. The original audit and proposal remain historical baseline documents.

## Runtime and access

Use the locked backend requirements and the frontend Node engine requirement. V2 reads only `REVIEW_*` environment settings; the old `OPENAI_*`/`MOCK_MODE` configuration cannot silently enable generation. Missing configuration yields a disabled service or a fail-closed configuration error. No keys or existing `.env` values were copied into the new system.

Access uses operator-provisioned random bearer tokens with at least 32 characters. A principal record has `id`, `workspace_id`, `role` and SHA-256 of the token. Generate with a cryptographically secure generator (for example Python `secrets.token_urlsafe(40)`); transmit through your approved secret channel, never commit it. Configure only the digest. Revocation/rotation currently requires changing the principal list and restarting API processes. Browser tokens are memory-only and cleared on logout/reload; in-flight requests abort on sign-out.

This is a bounded operator-controlled identity foundation. Production SSO, expiring sessions, rotation workflow, audit of membership changes and shared-document grants are not implemented. All documents are strictly owner-scoped even within a workspace. Viewers cannot mutate records; reviewer/owner roles may act only on their own documents. Do not provision multiple people with one token or user ID.

## Schema and legacy isolation

The default v2 store is `data/review-v2/reviews.sqlite3`. `python -m app.review.store` explicitly initializes it. The API does not create tables on startup. It never opens the old contracts database, Chroma or upload directories. `schema_version` is checked by readiness. Schema 1 is a new-store bootstrap, not a legacy migration framework.

The default Compose volume is new (`review_v2`). Never point it at an existing data directory without an inventory and a migration/recovery plan. Legacy users/documents have no reliable ownership mapping, so no automatic reassignment is attempted. Old API routes are not mounted by `app.main`. Retained legacy modules are regression-history code, not supported service entry points.

For an eventual migration, export an inventory without exposing document content, map each document to an authorized owner with explicit review, assign retention, transform source/run records on synthetic rehearsal data, back up and validate restores, then import in a separate reviewed migration. Unknown owners remain inaccessible. No production/legacy migration was run here.

## Worker

Start `python -m app.review.jobs` with the same environment and v2 volume as the API. Jobs and document insertion commit in one SQLite transaction. Workers claim with a lease token and bounded attempt count, checkpoint source and validated results, and reject late results after cancellation/deletion. Each transaction opens/closes its own connection; no transaction remains open during parsing/provider calls. A process death is recovered after lease expiry (180 seconds). Owner-triggered retries preserve committed checkpoints; automatic provider retries are deliberately disabled to avoid uncontrolled duplicate costs.

Parser subprocesses have a wall-clock limit. Linux adds address-space/CPU limits; Compose worker adds no network, dropped capabilities, read-only root, memory/CPU caps and bounded temporary storage. A subprocess alone on Windows is not an OS security sandbox. Arbitrary upload remains disabled until the actual isolation deployment has been reviewed. Malware scanning and disarm are still pending. Do not equate a successful parse with safety.

The default no-network worker cannot use a live AI provider. Before changing that boundary, implement/review separated parser isolation and a restricted provider gateway. Never enable generic worker egress simply to make live mode work around the parser security boundary.

## Modes and gates

- `disabled`: no new sample or upload operation. Existing owner-authorized records may still be read.
- `demo`: only server-owned synthetic sample creation; never accepts arbitrary user files.
- `manual`: extraction and human annotations; no AI-generated findings. Upload also requires `REVIEW_UPLOAD_ENABLED` and approved parser isolation.
- `live`: requires explicit provider handling and evaluation approvals, HTTPS configuration, model/key and an adjudicated report matching the exact prompt/model/parser version. Still requires separately reviewed parser/gateway network architecture and the remaining pilot gates.

The included evaluation report intentionally fails its gate. Do not manufacture qualified reviewer names or metrics to activate live mode. Independent adjudication, held-out cases and semantic citation/claim quality cannot be replaced by a schema or substring validator.

Generation reserves each provider call against the document's call ceiling before sending. Batches/output tokens and total observations are bounded. A interrupted already-sent request may still incur cost; exactly-once external billing is not guaranteed. Per-document call counts are not a currency budget. Implement provider-specific cost accounting before paid pilots.

## Deletion and retention

The API tombstones the document and clears source/analysis/context/display name/hash, decisions and decision events in the same transaction. Reads, exports and new job commits are immediately denied. The worker then removes the tracked original and records purge completion; file-lock/storage errors remain pending for retry. Expired retention is processed by the same worker. Original uploads orphaned before the DB commit are swept after a one-hour grace period.

V2 does not persist vectors, Q&A answers, comparisons or exports. Source questions and comparison are computed on demand; HTML exports are generated in memory and downloaded by the user. Thus these features create no additional server-side content store to purge. Browser memory and user downloads are outside the file purge receipt; users must close/logout and manage downloaded files separately.

SQLite uses secure-delete for logical record clearing, but this is **not** a forensic-erasure guarantee for WAL pages, storage media snapshots or backups. The receipt covers active application records and tracked originals only. Apply encrypted storage, backup expiry and restore-time tombstone replay under a reviewed operator policy before promising full retention/deletion guarantees. The code does not erase legacy stores or provider copies. Live-mode provider retention text must be verified against the actual provider and contract.

## Monitoring and incidents

### Dependency lock maintenance

Resolve runtime and test dependencies separately from `backend/requirements.in` and `backend/requirements-test.in` using `pip-compile --strip-extras --output-file work/runtime-resolved.txt backend/requirements.in` (and the corresponding test paths). Then run `python backend/tools/hash_lock.py work/runtime-resolved.txt backend/requirements.txt` and the corresponding test paths. The helper attaches published artifact SHA-256 values from PyPI HTTPS metadata; pip verifies the selected distribution during `--require-hashes` installation. Review version changes, install the lock in an isolated environment, run tests and advisory scans. Conventional `pip-compile --generate-hashes` is also supported but can download many platform artifacts.

Current locks were resolved on Windows/Python 3.11. Linux container and hosted CI verification remain release requirements, including platform-specific dependency completeness. Refresh and scan packaging tools and base images as well as application dependencies; a clean requirements audit does not cover the operating system or container image.

`/api/health` is liveness; `/api/ready` checks the v2 schema/store without a paid call. Worker age, queue length, purge backlog, storage headroom and provider spend require monitoring outside those endpoints. Safe job-failure logs contain job ID and reason code, not document text or provider error payloads. Request limits are persisted per minute; keep API process counts/datastore capacity within tested bounds.

Suggested operator checks: queued/running jobs older than lease expiry, exhausted attempts, pending deletion age, parser failure reasons, AI-call reservations and repeated authorization failures. These are runbook requirements, not claims that an alerting service has been deployed.

On suspected disclosure or misleading results: disable uploads/live processing, isolate affected access, preserve restricted non-content event evidence, identify source/run versions, involve the security/product owner and qualified legal reviewer as appropriate, and validate a fix offline before restoring service. Revert to a known-good code/config version only if its schema and safeguards remain compatible. Do not restore old unauthenticated routes as a rollback.

## Restore rehearsal required before pilot

Use only synthetic data for rehearsal. Stop writes or take an SQLite-consistent backup (not an uncoordinated file copy), preserve tracked upload files, store encrypted backups separately, and test restoration into a fresh path. Replay tombstones before exposing restored data. Check foreign ownership denial, missing/orphan file reconciliation, lease recovery and export correctness. Measure actual RPO/RTO; the planned 24-hour/4-hour goals are not yet demonstrated.

Container execution, Linux resource boundaries, production reverse proxy/TLS, SSO, backup expiry, incident delivery and a restore drill remain unverified here. The local browser uses loopback-only synthetic services and is not a deployment.
