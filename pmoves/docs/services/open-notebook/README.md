# Open Notebook — Service Guide

Status: Compose add‑on (external image), attached to shared network.

Overview
- Lightweight notebook UI + API for local workflows. Lives on the shared `pmoves-net` so it can talk to services if needed.

Compose
- File: `pmoves/docker-compose.open-notebook.yml`
- Service: `open-notebook`
- Ports (host → container): UI `8503:8502`, API `5056:5055`
- Network: external `pmoves-net` (shared with the main stack)

Make targets
- `make up-open-notebook` — bring up ON on `pmoves-net` (UI http://localhost:8503, API :5056)
- `make down-open-notebook` — stop ON
- `make -C pmoves up-external` — starts the packaged image alongside Wger/Firefly/Jellyfin (ensure `docker network create pmoves-net` first)

Troubleshooting
- If port conflicts occur, adjust the host ports in `docker-compose.open-notebook.yml` (e.g., `8504:8502`, `5057:5055`).
- Ensure the shared network exists: `docker network create pmoves-net` (Make and Compose create/attach automatically when needed).
- Set credentials in `pmoves/.env.local` before starting:
  ```
  OPEN_NOTEBOOK_API_URL=http://open-notebook:5055
  OPEN_NOTEBOOK_API_TOKEN=<generated-token>
  ```
- Health checks:
  - UI: `curl -I http://localhost:8503` (expect 200)
  - API: `curl http://localhost:5056/healthz` (returns `{ "ok": true }`)
- If PMOVES logs complain that Open Notebook is missing, re-run `make bootstrap` after the service is up so the env loader captures the API URL/token. Restart `notebook-sync` with `docker compose --profile orchestration up -d notebook-sync`.

Notes
- ON is optional and does not participate in core smokes.
- Data stores live under `pmoves/data/open-notebook/`; remove the SQLite or SurrealDB files there if you want a clean reset.
