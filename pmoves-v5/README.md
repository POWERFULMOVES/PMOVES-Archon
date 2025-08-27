# PMOVES v5.6 — Full pre‑VM stack

Profiles:
- core: NATS + n8n
- data: Neo4j + Qdrant + MinIO + Supabase CE
- agents: Agent-Zero + Archon
- workers: analysis-echo + graph-linker + publisher
- gen: Ollama + ComfyUI + comfy-watcher
- media: Jellyfin
- ops: minio-bootstrap
- obs: Prometheus + Grafana

## Quickstart
cp .env.example .env
docker compose --profile core --profile data up -d
docker compose --profile agents up -d
docker compose --profile workers up -d

# Optional
docker compose --profile gen up -d
docker compose --profile media up -d jellyfin
docker compose --profile obs up -d

## n8n workflows
Import from /services/n8n/workflows:
- pmoves_echo_ingest.json
- pmoves_comfy_gen.json
- pmoves_content_approval.json

## Content Publishing
- Approval webhook → publishes `content.publish.approved.v1` via Agent-Zero.
- Publisher listens, downloads from MinIO to shared `/library/images`, triggers Jellyfin scan, emits `content.published.v1`.

