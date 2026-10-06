# Azure upgrade plan — Contract Risk Analyzer

Goal: run the existing app on Azure with production engineering around it (IaC, CI/CD,
evals, observability), **without changing what the product does**. Every phase must keep
the current local / Contabo setup working (local backends stay the default).

## Current state (reviewed 2026-10-06)
- FastAPI backend (`backend/app`), React/Vite frontend, ~3k lines Python.
- LLM: `OpenAI(api_key, base_url)` in `services/risk_analyzer.py:322`, model `gpt-4o-mini`
  via `config.Settings`. `openai==1.51.0` pinned with `httpx==0.27.2` (newer httpx breaks it).
- DB: SQLite hard-coded in `database.py` (`sqlite:///./data/contracts.db`), SQLAlchemy sync.
- Files: written to `./data/uploads` in `routers/upload.py` and `routers/compare.py`.
  `compare.py` builds the path from the raw client filename (`f"{id}_a_{file_a.filename}"`);
  `upload.py` does the same. Should use a sanitized name.
- Vector store: ChromaDB `PersistentClient("./chroma")`, default local embedding function,
  one collection per document (`services/vector_store.py`).
- Background work: FastAPI `BackgroundTasks` (in-process).
- Tests: `backend/tests/test_calibration.py`, `test_jev_judge.py`. No CI.

## Target
```
GitHub Actions: lint + tests + evals -> build image -> GHCR -> Azure Container Apps
Frontend -> Azure Static Web Apps
Backend (Container Apps, managed identity) -> Azure OpenAI (chat + embeddings)
                                          -> Azure AI Search (vector index, replaces Chroma)
                                          -> Azure Blob Storage (uploads)
                                          -> Azure Database for PostgreSQL (replaces SQLite)
                                          -> Application Insights (OpenTelemetry)
All infra in Bicep (infra/), GitHub -> Azure login via OIDC, budget alert.
```

## Phase 1 — Cloud-ready code, local only (no Azure account needed)
Selected by env vars; defaults keep today's behaviour exactly.
1. **Config**: add `database_url` (default the current SQLite URL), `storage_backend`
   (`local` | `azure_blob`), `vector_backend` (`chroma` | `azure_search`), `llm_provider`
   (`openai` | `azure_openai`) + the Azure settings each needs (endpoint, deployment names,
   api version, container/index names). Azure auth should support `DefaultAzureCredential`
   (managed identity) with an optional key fallback.
2. **Database**: `database.py` reads `settings.database_url`; only pass
   `check_same_thread` for SQLite. Add `psycopg[binary]` so Postgres works.
3. **Storage interface** (`services/storage.py`): `save(name, bytes) -> ref`,
   `local_path(ref)` (context manager that yields a readable temp path for the parsers).
   `LocalStorage` (current behaviour) and `AzureBlobStorage`. Sanitize filenames
   (basename only, safe characters) in both routers.
4. **Vector store interface**: keep the same `store_chunks(doc_id, chunks)` /
   `search(doc_id, query, n)` API. `ChromaStore` (current) and `AzureSearchStore`
   (one shared index with a `doc_id` filter field, embeddings from Azure OpenAI).
5. **LLM client factory**: one `get_llm_client()` returning `OpenAI` or `AzureOpenAI`;
   use it everywhere the client is built. Upgrade `openai` to a version that works with
   current httpx (>=1.55.3) and unpin httpx accordingly.
6. **Tests** (pytest, no network): settings defaults, filename sanitising, LocalStorage
   round-trip, DB URL handling, client factory picks the right class, vector-store
   factory picks the right backend. Azure SDK classes are mocked. Existing tests still pass.
7. **Tooling**: `ruff` config + fix lint; `requirements-dev.txt`; Dockerfile runs as a
   non-root user; `.env.example` lists every new variable with comments.
8. Do not commit `data/`, `chroma/`, `venv/`, `.env`.

## Phase 2 — Infrastructure as code (Bicep)
Constraints found 2026-10-06: the target is the **"Azure for Students"** subscription. Its policy
only allows `austriaeast, polandcentral, switzerlandnorth, belgiumcentral, swedencentral`, so
everything goes in **swedencentral**. Static Web Apps is not offered in those regions, so the
**frontend runs as a second Container App** built from `frontend/Dockerfile` (nginx). The same
Azure login can also see VU university subscriptions: every script must pass
`--subscription "Azure for Students"` explicitly.

`infra/main.bicep` (subscription scope, creates the resource group) + modules + params:
Log Analytics + App Insights; Container Apps environment; backend app (system-assigned managed
identity, external ingress on 8000, scale 0-1) and frontend app; Azure OpenAI account + chat and
embedding deployments; AI Search (free tier); Storage account + `uploads` container; PostgreSQL
Flexible Server (Burstable B1ms) + database; role assignments for the backend identity (Storage
Blob Data Contributor, Search Index Data Contributor, Cognitive Services OpenAI User); budget alert
(EUR 10/month). Plus a script that creates the AI Search index, and one-command deploy / what-if /
teardown scripts.

## Phase 3 — CI/CD (GitHub Actions)
PR: ruff, pytest, quick eval subset. Main: build backend image -> GHCR -> update Container
App; frontend via Static Web Apps action. Azure login via OIDC federated credential.

## Phase 4 — Evaluation suite
`evals/` golden set: contracts with labelled risky clauses + Q&A pairs. Metrics: risky-clause
recall/precision, retrieval hit rate@k for Q&A, answer groundedness, score stability across
runs. Markdown report; CI fails below agreed thresholds.

## Phase 5 — Observability
`azure-monitor-opentelemetry`; spans per pipeline step (parse, split, embed, analyse, score,
Q&A); tokens, cost and latency per request; one App Insights workbook/dashboard.

## Phase 6 — Cutover and write-up
Point contracts.manarattar.com at Azure (keep Contabo one week as fallback). Case study on
manarattar.com (architecture, eval results, monthly cost). CV/LinkedIn line.
