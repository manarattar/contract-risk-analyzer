# Case study: moving a contract risk analyzer to Azure

**Live:** https://azure-contracts.manarattar.com (Azure). The original version at
contracts.manarattar.com is a separate deployment and is unchanged.

## The product

Upload a contract (PDF, DOCX, TXT). The backend splits it into clauses, scores each one for risk with
an LLM, flags missing clauses and contradictions, and produces a PDF report. A Q&A box answers
questions about the contract with retrieved source clauses.

## Goal

Turn a working single-server app into something that looks like production work on Azure:
infrastructure as code, keyless authentication, CI/CD, measurable quality, and observability, on an
Azure for Students subscription.

## Architecture

```
Browser ── HTTPS ── Caddy (Contabo, TLS) ── Container App: frontend (nginx, public)
                                                  │  /api proxy
                                                  ▼
                                           Container App: backend (FastAPI, internal only)
                                             │ user-assigned managed identity
             ┌───────────────┬───────────────┼────────────────┬──────────────────┐
             ▼               ▼               ▼                ▼                  ▼
      Azure OpenAI     Azure AI Search   Blob Storage   PostgreSQL Flexible   App Insights
   gpt-5-mini + emb.   (vector search)   (uploads)         (B1ms)          (OpenTelemetry)
```

- **Infrastructure:** Bicep at subscription scope (`infra/`): resource group, Container Apps
  environment, both apps, OpenAI with two deployments, AI Search (free tier), Storage, Postgres,
  Log Analytics, App Insights, workbook, a EUR 10 budget alert, and the GitHub deploy identity.
- **No secrets for Azure services:** the backend reaches OpenAI, Search and Storage through a
  managed identity with data-plane roles. Shared-key access on Storage and key auth on OpenAI are
  disabled. The only secret is the Postgres connection string.
- **CI/CD:** GitHub Actions logs in to Azure with OIDC (a federated credential on a user-assigned
  identity, limited to the repo's `azure` environment). Each push runs lint/tests/Bicep build,
  builds both images to GHCR, updates the Container Apps, and ensures the search index exists.

## Constraints and how they shaped the design

| Constraint | Decision |
|---|---|
| The subscription sits in a university Entra tenant: no app registrations | OIDC through a **user-assigned managed identity** with a federated credential, instead of a service principal |
| Region policy allows 5 EU regions only | Everything in Sweden Central |
| New Container Apps environments are created in **Express** mode, and Standard mode is not offered in any allowed region | Express does not support system-assigned identities, so the backend uses a user-assigned one. Express does not support custom domains, so Caddy on my existing VPS terminates TLS for the subdomain and forwards to Azure (Front Door would have cost ~EUR 35/month) |
| `gpt-4o-mini` 2024-07-18 rejected as deprecating, zero quota for `gpt-5.4-mini` | `gpt-5-mini`, which also needed `temperature` removed (`LLM_USE_TEMPERATURE=false`) |
| 10K tokens/minute quota | Rate-limit retries; a full eval run takes ~15 minutes |
| Student credit | Postgres is the main cost (~EUR 15-20/month); scripts stop and start it between demos |

## Quality: an evaluation suite instead of spot checks

`backend/evals` holds 6 labelled contracts (every clause has a High/Medium/Low label), 18 Q&A pairs,
and expected missing clauses. One run measures risky-clause precision and recall, risk-level
accuracy, missing-clause recall, retrieval hit rate, answer keywords, groundedness (an LLM judge),
and score stability across repeated runs. CI fails if any metric drops below its floor.

The suite paid off twice:

1. **It found a real weakness.** The model never raised false alarms (precision 1.0) but missed
   risky clauses (recall 0.85). The prompt only guarded against false positives. Adding general
   red-flag patterns raised recall to 1.0 and F1 from 0.92 to 0.97, at the cost of one false alarm.
   A contract added after the baseline, and not used for tuning, was scored correctly.
2. **It caught a measurement mistake.** The first local run reported recall 0.69, but a local Jev
   API key meant it measured a different classifier from production. Evals now run in CI, where the
   environment matches production.

Details: `docs/evals/README.md`.

## Observability

OpenTelemetry through `azure-monitor-opentelemetry`, active only when App Insights is configured:
a span per pipeline step (parse, split, analyse with detect/clauses/contradictions/missing/score,
embed and index, Q&A search and answer), and per LLM call: model, stage, input/output tokens,
latency, 429 retries and estimated cost. An App Insights workbook (Bicep) shows failure rate,
p50/p95 latency per step, tokens and cost per stage per day, retries, and exceptions.
Details: `docs/observability.md`.

## Process

I planned and reviewed each phase; OpenAI Codex wrote most of the code against written specs, and
I verified every change (ruff, 59 offline tests, Bicep build, live end-to-end runs) before
committing. Review caught real issues: a heading that leaked an eval label to the model,
macro-averaged metrics that inflated recall, an Express-mode identity failure, and the Jev confound.

## What I would do next

- Harder and more varied Q&A pairs; current retrieval scores are at the ceiling.
- Raise missing-clause recall (0.75), the weakest metric.
- Track one more false-positive-heavy contract so precision has more than one test.
- Move to a subscription with Standard Container Apps environments to drop the VPS proxy.
