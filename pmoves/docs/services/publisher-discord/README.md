# publisher-discord — Service Guide

Status: Implemented (compose)

Overview
- Publishes selected events to Discord via webhook.

Compose
- Service: `publisher-discord`
- Port: `8094:8092`
- Profiles: `orchestration`, `agents`
- Depends on: `nats`

Environment
- `DISCORD_WEBHOOK_URL`
- `NATS_URL` (default `nats://nats:4222`)
- `DISCORD_SUBJECTS` (default `ingest.file.added.v1,ingest.transcript.ready.v1,ingest.summary.ready.v1,ingest.chapters.ready.v1`)

Smoke
```
docker compose --profile agents up -d nats publisher-discord
docker compose ps publisher-discord
docker compose logs -n 100 publisher-discord | rg -i "connected|NATS" || true
```
