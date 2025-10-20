# Open Notebook — Service Guide

Status: Compose add‑on (external image), attached to shared network.

Overview
- Lightweight notebook UI + API for local workflows. Lives on the shared `pmoves-net` so it can talk to services if needed. Host ports are overridable so the UI/API can coexist with other stacks.

Compose
- File: `pmoves/docker-compose.open-notebook.yml`
- Service: `open-notebook`
- Ports (host → container):
  - UI `${OPEN_NOTEBOOK_UI_PORT:-8503}:8502`
  - API `${OPEN_NOTEBOOK_API_PORT:-5055}:5055`
- Network: external `pmoves-net` (shared with the main stack)

Make targets
- `make up-open-notebook` — bring up ON on `pmoves-net` (UI http://localhost:${OPEN_NOTEBOOK_UI_PORT:-8503}, API :${OPEN_NOTEBOOK_API_PORT:-5055})
- `make down-open-notebook` — stop ON
- `make -C pmoves up-external` — starts the packaged image alongside Wger/Firefly/Jellyfin (ensure `docker network create pmoves-net` first)

Troubleshooting
- If port conflicts occur, set `OPEN_NOTEBOOK_UI_PORT` / `OPEN_NOTEBOOK_API_PORT` in `.env.local` (or export inline) before running Make/Compose.
- Ensure the shared network exists: `docker network create pmoves-net` (Make and Compose create/attach automatically when needed).
- Set credentials in `pmoves/.env.local` before starting:
  ```
  OPEN_NOTEBOOK_API_URL=http://open-notebook:5055
  OPEN_NOTEBOOK_API_TOKEN=<generated-token>
  ```
- Health checks:
  - UI: `curl -I http://localhost:${OPEN_NOTEBOOK_UI_PORT:-8503}` (expect HTTP 200/307)
  - API: `curl http://localhost:${OPEN_NOTEBOOK_API_PORT:-5055}/health` (returns `{ "status": "healthy" }`)
- If PMOVES logs complain that Open Notebook is missing, re-run `make bootstrap` after the service is up so the env loader captures the API URL/token. Restart `notebook-sync` with `docker compose --profile orchestration up -d notebook-sync`.

Notes
- ON is optional and does not participate in core smokes.
- Data stores live under `pmoves/data/open-notebook/`; remove the SQLite or SurrealDB files there if you want a clean reset.
