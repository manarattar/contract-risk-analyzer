# Deploying AI Contract Risk Analyzer

**Live at `contracts.manarattar.com`.**

## How it is put together

Vite SPA served by Caddy; FastAPI proxied at `/api/*` on the same origin, so
there is no CORS configuration to maintain.

## Where this runs

Everything is on a single Contabo VPS. There is no Vercel, Render, or other
PaaS involved any more.

| | |
|---|---|
| Server | `194.163.176.183` — `ssh ubuntu@194.163.176.183` (key only, no password) |
| Stack | `/srv/stack/docker-compose.yml` + `/srv/stack/Caddyfile` |
| App sources | `/srv/apps/<name>` |
| Built static sites | `/srv/www/<name>` |
| Secrets | `/srv/stack/env/<name>.env` (0600, root-owned) |
| Database | one `postgres:18-alpine` container, internal network only |
| TLS | Caddy, automatic Let's Encrypt |
| Backups | nightly 03:17 to `/srv/backup/nightly`, 14-day rotation |

Caddy terminates TLS for every hostname and routes by host. Postgres has no
published port — it is reachable only on the internal Docker network.

## Secrets

Never commit them. Each app reads `/srv/stack/env/<name>.env` on the server,
which compose injects via `env_file`. `DATABASE_URL` is set by compose, not by
that file, so an app cannot accidentally point at an old database.

## Deploying a change

```bash
# frontend — VITE_API_URL must be set explicitly, see gotchas
cd frontend && VITE_API_URL="https://contracts.manarattar.com" npm run build
tar czf - -C dist . | ssh ubuntu@194.163.176.183 \
  'rm -rf /srv/www/contracts && mkdir -p /srv/www/contracts && tar xzf - -C /srv/www/contracts'

# backend
cd ../backend && tar czf - --exclude=venv --exclude=.env --exclude=chroma --exclude=data . \
  | ssh ubuntu@194.163.176.183 'tar xzf - -C /srv/apps/contracts'
ssh ubuntu@194.163.176.183 'cd /srv/stack && sudo docker compose up -d --build contracts'
```

## Things that will catch you out

- **`VITE_API_URL` must be set at build time.** Unlike the other frontends this
  one falls back to `http://localhost:8000`, not a relative path, so an unset
  value ships a build that calls the visitor's own machine.
- This is the only memory-heavy app: ChromaDB loads a local ONNX embedding model.
  It gets a 1 GB limit and persistent volumes for `/app/chroma` and `/app/data`.
  That on-disk vector store is why serverless hosting was never viable.
- `backend/venv/` is committed to this repo. Keep it out of the upload and out of
  the Docker build context or the image balloons.

## Rolling back

Rebuild from the previous commit and redeploy. There is no rollback to a
previous provider — the old Vercel and Render deployments were deleted in
September 2026. Database backups are on the server at
`/srv/backup/nightly` (nightly, 14-day rotation).
