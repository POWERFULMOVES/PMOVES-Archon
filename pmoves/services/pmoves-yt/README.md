# PMOVES.YT — Ingest + CGP Publisher

YouTube ingest helper that emits CHIT geometry after analysis.

## Service & Ports
- Compose service: `pmoves-yt`
- Starts with `make up-yt` (brings up `ffmpeg-whisper` too)

## Geometry Bus (CHIT) Integration
- Publishes `geometry.cgp.v1` to the Hi‑RAG gateway:
  - Endpoint: `POST ${HIRAG_URL}/geometry/event`
- Environment:
  - `HIRAG_URL` — base URL for the geometry gateway (`http://localhost:8086` by default)

## Smoke
- See `pmoves/services/pmoves-yt/tests/test_emit.py` for the CGP emission assertion.
- Run the main smokes in `pmoves/docs/SMOKETESTS.md` after `make up`.

## Resilient Playlist Ingest (2025-10)
- `/yt/playlist` now runs downloads concurrently (bounded by `YT_CONCURRENCY`) with
  an async worker pool and coordinated rate limiting (`YT_RATE_LIMIT`).
- Transient errors (network, 5xx, yt-dlp hiccups) retry with exponential backoff
  up to `YT_RETRY_MAX` attempts; state updates live in Supabase (`yt_items`).
- Downloads resume automatically thanks to a persistent scratch directory
  (`YT_TEMP_ROOT`, default `/tmp/pmoves-yt`). Successful ingests clean the cache;
  failures leave partial files to resume on the next run.
- Summaries/chapters emit `ingest.summary.ready.v1` / `ingest.chapters.ready.v1`
  events so downstream automations (Discord, n8n) can react in real time.
