# Phase 2 Azure infrastructure

The subscription-scope template creates `rg-contract-analyzer` in `swedencentral` by default. Its location parameter is restricted to the five regions allowed by the Azure for Students policy. The frontend and backend are Container Apps in the same environment. Only the frontend has external ingress; the backend is reachable through its internal HTTPS FQDN. The deployment outputs that FQDN and the frontend URL, OpenAI endpoint, Search endpoint, and Blob account URL.

## Prerequisites

- Azure CLI and access to the **Azure for Students** subscription. Every CLI call in these scripts passes `--subscription 'Azure for Students'` explicitly.
- Permission to create resource groups, resources, role assignments, and a resource-group Consumption budget. A read-only what-if completed with 20 creates and no policy errors. Azure OpenAI model availability and quota still require confirmation at deployment.
- A PostgreSQL administrator password and at least one budget notification email. The scripts prompt for these when omitted; they are never stored in tracked files. The scripts place the password in a process-local environment variable for Bicep parameter evaluation and clear it afterward; it is never passed as a command-line argument.

## Review and deploy

From the repository root in PowerShell:

```powershell
./infra/whatif.ps1 -AdminLogin craadmin -ContactEmails @('you@example.com')
./infra/deploy.ps1 -AdminLogin craadmin -ContactEmails @('you@example.com')
```

Both commands prompt for the PostgreSQL password. To supply it from an existing secure string, use `-AdminPassword $securePassword`. `-ResourceGroupName` and `-Location` can override defaults. Both scripts also accept `-BackendImage`, `-FrontendImage`, `-ChatCapacity`, and `-EmbeddingCapacity` (capacity defaults are 10 thousand tokens/minute each). Azure chat now defaults to `gpt-5.4-mini` version `2026-03-17` (GlobalStandard) because Azure rejects new deployments of `gpt-4o-mini` version `2024-07-18` with `ServiceModelDeprecating`. The backend sets `LLM_USE_TEMPERATURE=false` for this GPT-5-family model. Override the model through `CRA_CHAT_MODEL_NAME` and `CRA_CHAT_MODEL_VERSION` when building the parameter file. The default public placeholder image lets the infrastructure deploy before application images exist; the application will only work after deploying its real images. The frontend image should be built from `frontend/Dockerfile`, which defaults `BACKEND_URL` to `http://backend:8000` for Docker Compose and receives the internal HTTPS backend URL from Container Apps.

The scripts set `CRA_POSTGRES_ADMIN_LOGIN`, `CRA_POSTGRES_ADMIN_PASSWORD`, comma-separated `CRA_CONTACT_EMAILS`, image and capacity variables only in their current process, then deploy through `main.bicepparam` and clear those variables in a `finally` block. Manual parameter-file deployment must set these variables in the current process. Do not commit generated ARM parameter JSON, logs, or passwords.

## After deploying real images

Create the shared AI Search vector index from a workstation with Search Index Data Contributor permission or a Search admin key:

```powershell
$env:AZURE_SEARCH_ENDPOINT = '<searchEndpoint output>'
$env:AZURE_SEARCH_INDEX = 'contract-chunks'
cd backend
python scripts/create_search_index.py
```

`DefaultAzureCredential` is used unless `AZURE_SEARCH_KEY` or `--key` is supplied. The backend identity has **Search Index Data Contributor** to read and write index documents, which does not grant permission to create the index. It also has Storage Blob Data Contributor and Cognitive Services OpenAI User at the relevant resource scopes. Azure RBAC changes can take time to propagate.

`DATABASE_URL` is installed as a Container App secret. Storage shared-key access and OpenAI local-key auth are disabled. The budget amount is `10` in the subscription's billing currency; Azure determines whether that is EUR.

## Costs and demo schedule

| Resource | Rough monthly cost while running |
| --- | ---: |
| PostgreSQL Flexible Server, Burstable B1ms with 32 GB storage | ~EUR 15�20; main cost |
| AI Search | Free tier |
| Azure OpenAI | Usage based; cents for small demos |
| Container Apps, Log Analytics, App Insights, Blob Storage | Free allowances or cents at small demo usage |

These are planning estimates, not a quote; actual billing and free allowances depend on usage and subscription terms. The EUR 10 budget alerts do not cap spending. Stop the DB between demos and start it before the next demo:

```powershell
./infra/stop-db.ps1
./infra/start-db.ps1
```

Both scripts find the Flexible Server in the named resource group and pass `--subscription 'Azure for Students'` on every Azure CLI call. Database-backed application requests fail while the server is stopped.

## Known trade-offs

The `AllowAzureServices` (`0.0.0.0`) PostgreSQL firewall rule permits any Azure-hosted client to attempt connections; the admin password and TLS are still required. VNet integration and private endpoints are the production upgrade.

## Remove resources

```powershell
./infra/teardown.ps1 -ResourceGroupName rg-contract-analyzer
```

This deletes the resource group and all resources in it. Run it only when the environment is no longer needed.
