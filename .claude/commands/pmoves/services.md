---
name: pmoves:services
description: Service catalog with status, ports, and health information
---

Display comprehensive PMOVES.AI service information.

## Usage

```bash
/pmoves:services [filter] [--json] [--health]
```

**Options:**
- `filter` - Filter by tier (data, api, workers, agents, monitoring, gpu, etc.)
- `--json` - Output as JSON instead of formatted table
- `--health` - Check healthz endpoints for all services

## Examples

```bash
# Show all services
/pmoves:services

# Filter by tier
/pmoves:services agents
/pmoves:services workers,data

# JSON output for scripting
/pmoves:services --json | jq '.services | map(select(.status == "running"))'

# Check health of all services
/pmoves:services --health
```

## Implementation

```bash
cd pmoves && docker compose ps --format json | jq -r '
  [
    foreach .[] as $service (
      {
        "name": $service.Name,
        "state": $service.State,
        "ports": ($service.Ports // "" | split(",") | map(trim)),
        "networks": ($service.Networks // "" | split(",") | map(trim)),
        "profile": ($service.Labels // {} | if .["com.docker.compose.project.working_dir"] then split("/") | .[-1] else "default" end)
      }
    )
  ] | {services: .}
'
```

## Service Tiers

- **data**: Supabase, Qdrant, Neo4j, Meilisearch, MinIO
- **api**: Hi-RAG v2, TensorZero Gateway, Presign
- **workers**: Extract, LangExtract, media analyzers
- **agents**: Agent Zero, Archon, Mesh Agent
- **orchestration**: SupaSerch, DeepResearch
- **monitoring**: Prometheus, Grafana, Loki
- **gpu**: GPU-accelerated services
- **yt**: PMOVES.YT ingestion
- **ui**: Frontend UIs

## Health Check Endpoints

When using `--health`, checks these endpoints:

| Service | Health Endpoint |
|---------|----------------|
| Agent Zero | http://localhost:8080/healthz |
| Archon | http://localhost:8091/healthz |
| Hi-RAG v2 CPU | http://localhost:8086/healthz |
| Hi-RAG v2 GPU | http://localhost:8087/healthz |
| SupaSerch | http://localhost:8099/healthz |
| DeepResearch | http://localhost:8098/healthz |

## Notes

- Requires `jq` for JSON output
- Uses docker compose ps for real-time status
- Parses service labels to determine profiles
- Port mappings extracted from published ports
