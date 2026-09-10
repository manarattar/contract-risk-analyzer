# Contract Review Assistant — Review desk

**Live public synthetic demo:** https://contracts.manarattar.com/. Private uploads and live AI remain disabled. See `docs/production-readiness/deployment/README.md` for the verified release, evidence and remaining gates.

An evidence-first workspace for human contract review. This implementation is a **local/demo release candidate, not an approved confidential pilot**. It provides authenticated owner-scoped reviews, saved source text, durable processing, human annotations and decisions, extractive source questions, candidate text comparison and escaped HTML export.

AI output is not legal advice. There are no signing recommendations, legal-confidence gauges or score-based winners in the v2 interface. Demo output is explicitly synthetic. Live generation and uploads fail closed unless their explicit settings are supplied.

## Start safely

Use Python 3.11 and Node 22.12 or newer. Install backend dependencies with `python -m pip install --require-hashes -r backend/requirements.txt`, and frontend dependencies with `npm ci`. Use a new virtual environment; do not reuse an unverified production environment.

1. Provision a high-entropy access token per user. Store its SHA-256 digest, user ID, workspace ID and role in `REVIEW_PRINCIPALS_JSON`. See `.env.example` for fields. Do not use shared or production tokens for local tests.
2. Export the `REVIEW_*` environment variables in your shell, or provide `.env` to Docker Compose. Python settings do not automatically load legacy `.env` files.
3. Set `REVIEW_MODE=demo`. Leave `REVIEW_UPLOAD_ENABLED=false`. An empty principal list denies all document access.
4. From `backend`, explicitly initialize the **new** datastore with `python -m app.review.store`. This command creates only the configured v2 schema; no old contracts or ownership are migrated.
5. Start API: `uvicorn app.main:app --host 127.0.0.1 --port 8000`.
6. In a second terminal with the same environment, start the durable worker: `python -m app.review.jobs`.
7. From `frontend`, run `npm run dev`. The development server proxies `/api` to the local backend. Open the workspace with your token and choose the synthetic example.

The browser keeps its token only in memory. Refresh requires signing in again; saved document routes and server-side review records persist. This operator-issued token model is a local pilot foundation, not a replacement for production SSO, rotation and session policy.

## Containers

`docker-compose.yml` uses a new `review_v2` volume and loopback-only ports. After configuring `.env`, run `docker compose --profile setup run --rm initialize` deliberately, then start the selected services. The default worker has no network, a read-only root, dropped capabilities and resource limits. It supports demo/manual processing; live provider access needs a separately reviewed network/gateway design. No containers were deployed by the implementation work.

## Verification

Install `backend/requirements-test.txt` with `--require-hashes` in the test environment first. From `backend`: `python -m pytest -p no:cacheprovider -q`. Live integration tests are excluded by default. From `frontend`: `npm run lint` and `npm run build`. Dependency and CI definitions are included. See `docs/production-readiness/implementation-status.md` for actual results and remaining gates.

## Boundaries

- v2 routes live under `/api/v2`; old unauthenticated routes are not mounted. Legacy modules remain for historical regression tests, not for deployment entry points.
- Existing SQLite/Chroma/uploads are not opened or assigned to users. Migration requires explicit ownership mapping, retention review and a tested migration procedure.
- PDF and DOCX parsing preserve extracted source locations with limitations. Original-page rendering, OCR, semantic clause alignment and qualified legal evaluation are not complete.
- Q&A shows matching passages, including an abstention on no match. It does not invent a factual answer from an empty result.
- Active deletion revokes access, clears stored review content and queues original-file purge. External backups, provider copies and downloaded exports are not falsely described as erased.

Start with [implementation status](docs/production-readiness/implementation-status.md), [audit and plan](docs/production-readiness/README.md), and [operations](docs/production-readiness/operations.md).
