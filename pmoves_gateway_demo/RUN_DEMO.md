# PMOVES Gateway Demo

## Install
pip install -r requirements-demo.txt

## Run
uvicorn gateway.main:app --reload

## Try
- http://localhost:8000/demo/shapes-webrtc (open in two tabs)
- http://localhost:8000/web/client.html
- http://localhost:8000/docs (Swagger)

## New: Offline Workflow Demo

Run a one‑shot PMOVES → CHIT flow (ingest → decode → calibrate → visualize) without external services:

```bash
curl -s http://localhost:8000/workflow/demo_run \
  -H "content-type: application/json" \
  -d '{"per_constellation": 20}' | jq
```

The response includes:

- `shape_id` and a `data_url` of the persisted CGP (`/data/{id}.json`).
- Geometry‑only decoded text per constellation.
- Paths to calibration artifacts and a link to the SVG renderer.

## APIs
POST /geometry/event
POST /geometry/decode/text
POST /geometry/calibration/report
POST /workflow/demo_run
GET  /shape/point/{id}/jump
