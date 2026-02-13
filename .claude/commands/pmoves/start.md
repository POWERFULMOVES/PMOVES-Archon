---
name: pmoves:start
description: Unified PMOVES.AI startup with preset configurations
---

Start PMOVES.AI services with intelligent preset selection.

## Usage

```bash
/pmoves:start [preset]
```

**Presets:**
- `minimal` - Core data + workers only
- `standard` - Core data + workers + agents (default)
- `full` - Everything including monitoring
- `dev` - Standard + UI development mode
- `gpu` - Standard with GPU services

## What It Does

1. **Checks prerequisites** - Verifies Docker and environment setup
2. **Prompts for preset** - Interactive selection (defaults to `standard`)
3. **Starts services** - Uses appropriate Makefile targets
4. **Shows progress** - Indicates which services are starting
5. **Validates health** - Checks healthz endpoints after startup
6. **Displays URLs** - Shows helpful UIs, APIs, and dashboards

## Examples

```bash
# Quick standard start
/pmoves:start

# Minimal stack (data + workers only)
/pmoves:start minimal

# Full stack with monitoring
/pmoves:start full

# Development with UI
/pmoves:start dev

# With GPU services
/pmoves:start gpu
```

## Preset Details

| Preset | Services | Time |
|---------|-----------|-------|
| `minimal` | Supabase, NATS, data tier, extract, langextract | ~2 min |
| `standard` | `minimal` + Agent Zero, Archon, Hi-RAG v2 | ~3 min |
| `full` | `standard` + monitoring stack (Prometheus, Grafana, Loki) | ~4 min |
| `dev` | `standard` + UI development mode (hot reload) | ~3 min |
| `gpu` | `standard` + GPU-accelerated services (Hi-RAG v2 GPU, FFmpeg-Whisper, media analyzers) | ~5 min |

## Output URLs

After startup, displays access URLs:

- **Grafana**: http://localhost:3002
- **Agent Zero UI**: http://localhost:50051
- **Archon UI**: http://localhost:8091
- **PMOVES UI**: http://localhost:4482

## Implementation

Wraps existing Makefile targets intelligently:
- `make up` - Core data + workers
- `make up-agents-ui` - Adds agents and UIs
- `make up-monitoring` - Adds observability stack
- `make up-gpu` - Adds GPU services

## Notes

- First startup takes longer (image pulls, database initialization)
- GPU services require NVIDIA runtime
- Press Ctrl+C to cancel startup sequence
