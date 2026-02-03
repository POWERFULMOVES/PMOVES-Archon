# PMOVES.AI Subsystem Integration Guide

**Purpose:** Central reference for integrating PMOVES.AI modular subsystems including BoTZ, DoX, Tokenism, Voice Agents, and CHIT Geometry Bus.

**Last Updated:** 2026-01-31

---

## Quick Reference

| Subsystem | Location | Purpose | API Ports | Profile |
|-----------|----------|---------|-----------|---------|
| **BoTZ** | `PMOVES-BoTZ/` | MCP tools platform | 2091, 2093-2108 | `agents,bots` |
| **DoX** | `PMOVES-DoX/` | Document intelligence | 8092 | `media` |
| **Tokenism** | `PMOVES-ToKenism-Multi/` | Economic simulation | 8100/8504 | `agents,botz` |
| **Voice Agents** | `pmoves/services/flute-gateway` | TTS/voice communication | 8055/8056 | `media` |
| **Ultimate TTS** | `PMOVES-Ultimate-TTS-Studio/` | Multi-engine TTS | 7861 | `tts,gpu` |
| **CHIT Bus** | `pmoves/docs/PMOVESCHIT/` | Geometry fabric | - | - |

---

## Architecture Overview

PMOVES.AI implements a **modular subsystem architecture** where each subsystem maintains autonomy while contributing to collective intelligence through standardized communication protocols.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PMOVES.AI Orchestrator                              │
│                     (Agent Zero + TensorZero + NATS)                        │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
┌───────▼────────┐      ┌──────────▼─────────┐      ┌────────▼────────┐
│      BoTZ      │      │       DoX          │      │    Tokenism     │
│  (MCP Tools)   │      │  (Document Intel)  │      │ (Economic Sim)   │
└───────┬────────┘      └──────────┬─────────┘      └────────┬────────┘
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   │
                        ┌──────────▼─────────┐
                        │   CHIT Geometry    │
                        │      Bus (NATS)    │
                        └────────────────────┘
```

---

## Subsystem Details

### 1. BoTZ (MCP Tools Ecosystem)

**Location:** `/PMOVES-BoTZ/`

**Purpose:** Unified multi-agent MCP (Model Context Protocol) platform providing 17+ specialized tools for document processing, memory management, API testing, and vision-language processing.

**Key Features:**
- **17 MCP Servers**: Docling (PDF), Cipher Memory (System 1/2 reasoning), E2B Sandbox (code execution), VL Sentinel (vision), Postman MCP (API testing), n8n Agent (workflows)
- **Multi-agent orchestration** via mprocs with 5 thread types (Base, Parallel, Chained, Fusion, Zero Touch)
- **Security hooks** via `patterns.yaml` with pre/post-execution validation

**Integration Points:**

| Component | Endpoint | Purpose |
|-----------|----------|---------|
| Gateway | `http://localhost:2091` | Main MCP gateway |
| Cipher Memory | `http://localhost:2093` | System 1/2 reasoning |
| Docling | `http://localhost:2097` | PDF/DOCX processing |
| E2B Sandbox | `http://localhost:2098` | Secure code execution |

**NATS Subjects:**
- `botz.mcp.tool.executed.v1` - Tool execution events
- `botz.cipher.memory.*` - Memory operations

**Documentation:**
- `/PMOVES-BoTZ/AGENTS.md` - Agent configuration
- `/PMOVES-BoTZ/docs/MCP_IMPLEMENTATION_GUIDE.md` - MCP integration

**Quick Start:**
```bash
# From PMOVES.AI root
docker compose --profile agents --profile botz up -d

# Verify health
curl http://localhost:2091/healthz
```

---

### 2. DoX (Document Intelligence)

**Location:** `/PMOVES-DoX/`

**Purpose:** Document intelligence platform for extracting, analyzing, and structuring data from PDFs, spreadsheets, XML logs, and APIs with AI-powered insights.

**Key Features:**
- **Multi-format ingestion**: PDF, CSV, XML, OpenAPI specs
- **Dual storage**: SQLite (standalone) / Supabase (docked)
- **Vector search**: FAISS/NumPy for semantic retrieval
- **CHIT Integration**: Real-time geometry bus for visualizations
- **Hyperbolic visualizations**: Poincaré disk, 3D manifolds, Riemann Zeta

**Integration Points:**

| Component | Endpoint | Purpose |
|-----------|----------|---------|
| PDF Ingest | `http://localhost:8092` | Document processing |
| API | `http://localhost:8093` | REST API |
| NATS WebSocket | `ws://localhost:9222` (docked) / `ws://localhost:9223` (standalone) | Real-time updates |

**NATS Subjects:**
- `tokenism.cgp.>` - Consumes geometry packets
- `geometry.>` - Publishes geometry events

**CHIT Integration:**
- Contracts: `/PMOVES-DoX/backend/app/contracts/`
- Generates CHIT geometry packets for document embeddings

**Documentation:**
- `/PMOVES-DoX/README.md` (742 lines) - Comprehensive user guide
- `/PMOVES-DoX/ARCHITECTURE.md` - System architecture
- `/PMOVES-DoX/API_REFERENCE.md` - API documentation

**Quick Start:**
```bash
# Standalone mode
cd PMOVES-DoX
docker compose up -d

# Docked mode (from PMOVES.AI root)
docker compose --profile media up -d pdf-ingest
```

---

### 3. Tokenism (Token Economy Simulator)

**Location:** `/PMOVES-ToKenism-Multi/`

**Purpose:** Comprehensive token economy simulation and projection validation framework for cooperative food systems, integrated with real financial data from Firefly-iii.

**Key Features:**
- **5 smart contract models**: GroupPurchase, GroVault, FoodUSD, GroupoToken, LoyaltyPoints
- **5-year business simulations** with 260-week projections
- **Confidence scoring**: HIGH/MEDIUM/LOW for calibrations
- **Event-driven architecture** with pub/sub contracts
- **Firefly-iii integration** for real financial data

**Integration Points:**

| Component | Endpoint | Purpose |
|-----------|----------|---------|
| Simulator API | `http://localhost:8100` | Simulation engine |
| UI Dashboard | `http://localhost:8504` | Interactive visualization |

**NATS Subjects:**
- `tokenism.cgp.weekly.v1` - Weekly CGP exports to geometry bus
- `tokenism.cgp.ready.v1` - CGP packets available

**CHIT Integration:**
- Contracts: `/PMOVES-ToKenism-Multi/integrations/contracts/chit/`
  - `shape-attribution.ts` - Geometric shape analysis
  - `swarm-attribution.ts` - Collective intelligence
  - `cgp-generator.ts` - Geometry packet generation
  - `hyperbolic-encoder.ts` - Hyperbolic space encoding
  - `zeta-filter.ts` - Riemann Zeta filtering

**API Endpoints:**
```
POST /simulate          - Run economic simulation
POST /calibrate/firefly - Calibrate with Firefly-iii data
GET  /healthz           - Service health check
GET  /cgp/export        - Export CGP packets
```

**Quick Start:**
```bash
# From PMOVES.AI root
docker compose --profile agents --profile botz up -d tokenism-simulator tokenism-ui

# Run simulation
curl -X POST http://localhost:8100/simulate \
  -H "Content-Type: application/json" \
  -d '{"weeks": 260, "scenario": "baseline"}'
```

---

### 4. Voice Agents

#### Flute-Gateway

**Location:** `/pmoves/services/flute-gateway/`

**Purpose:** Multimodal voice communication layer with Pipecat integration for natural speech synthesis and processing.

**Key Features:**
- **Prosodic TTS**: Natural speech with intelligent pausing and emphasis
- **Real-time streaming**: WebSocket-based audio I/O
- **Multiple backends**: VibeVoice, Whisper, Ultimate-TTS integration
- **Pipecat pipeline**: Professional audio processing

**Integration Points:**

| Component | Endpoint | Purpose |
|-----------|----------|---------|
| HTTP API | `http://localhost:8055` | REST API |
| WebSocket | `ws://localhost:8056` | Real-time audio streaming |

**API Endpoints:**
```
POST /v1/voice/analyze/prosodic    - Analyze text for prosody
POST /v1/voice/synthesize/prosodic - Synthesize speech
GET  /v1/sessions                  - List voice sessions
POST /v1/sessions                  - Create voice session
```

**Quick Start:**
```bash
# Start voice services
docker compose --profile orchestration --profile media up -d flute-gateway

# Test synthesis
curl -X POST http://localhost:8055/v1/voice/synthesize/prosodic \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello PMOVES", "voice": "af_sky"}'
```

#### Ultimate-TTS-Studio

**Location:** `/PMOVES-Ultimate-TTS-Studio/`

**Purpose:** Multi-engine TTS platform with 7 engines and Gradio interface for high-quality text-to-speech synthesis.

**Supported Engines:**
- **Kokoro** - High-quality neural TTS
- **F5-TTS** - Emotional speech synthesis
- **KittenTTS** - Fast lightweight TTS
- **VoxCPM** - Chinese language support
- **VibeVoice** - Versatile voice synthesis
- **IndexTTS** - Low-latency synthesis
- **Higgs-Audio** - Experimental engine

**Integration Points:**

| Component | Endpoint | Purpose |
|-----------|----------|---------|
| Gradio UI | `http://localhost:7861` | Interactive interface |
| API | Gradio API endpoints | Programmatic access |

**Quick Start:**
```bash
# GPU required for most engines
docker compose --profile tts --profile gpu up -d ultimate-tts-studio

# Access UI
open http://localhost:7861
```

---

### 5. CHIT Geometry Bus

**Location:** `/pmoves/docs/PMOVESCHIT/`

**Purpose:** Universal geometric data fabric for hyperbolic encoding, swarm intelligence, and geometric reasoning across all PMOVES subsystems.

**Key Concepts:**
- **CGP (Compact Geometry Packets)** - Efficient geometry serialization
- **Hyperbolic encoding** - Knowledge structure in hyperbolic space
- **Dirichlet attribution** - Multi-source attribution
- **Swarm intelligence** - Self-organizing agents

**Integration Architecture:**

```
┌─────────────┐     CGP      ┌─────────────┐
│   Tokenism  │─────────────▶│   DoX       │
│  (Producer) │              │ (Consumer)  │
└─────────────┘              └─────────────┘
       │                           │
       │                           │
       ▼                           ▼
┌─────────────────────────────────────────┐
│         CHIT Geometry Bus (NATS)         │
│  Subjects: tokenism.cgp.*, geometry.*    │
└─────────────────────────────────────────┘
```

**Contract Locations:**
- Tokenism: `/PMOVES-ToKenism-Multi/integrations/contracts/chit/`
- DoX: `/PMOVES-DoX/backend/app/contracts/`
- Reference: `/pmoves/docs/PMOVESCHIT/GEOMETRY_BUS_INTEGRATION.md`

**NATS Subjects:**
```
tokenism.cgp.weekly.v1       - Weekly economic projections
tokenism.cgp.ready.v1         - CGP packets available
geometry.event.v1             - Geometry events
tokenism.*                    - Tokenism namespace
geometry.*                    - Geometry namespace
```

**Documentation:**
- `/pmoves/docs/PMOVESCHIT/GEOMETRY_BUS_INTEGRATION.md` - Technical integration
- `/pmoves/docs/PMOVESCHIT/Integrating Math into PMOVES.AI.md` - Mathematical foundations
- `/pmoves/docs/PMOVESCHIT/Human_side.md` - User-facing guide

---

## Cross-Subsystem Communication

### NATS Event Subjects

**Core PMOVES:**
```
claude.code.tool.executed.v1          # Claude CLI tool execution
botz.mcp.tool.executed.v1             # BoTZ MCP tool usage
```

**Research & Search:**
```
research.deepresearch.request.v1      # Deep research requests
research.deepresearch.result.v1       # Research results
supaserch.request.v1                  # SupaSerch requests
supaserch.result.v1                   # SupaSerch results
```

**Geometry Bus:**
```
tokenism.cgp.weekly.v1                # Economic CGP exports
tokenism.cgp.ready.v1                 # CGP availability
geometry.event.v1                     # Geometry events
```

**Media Ingestion:**
```
ingest.file.added.v1                  # New file ingested
ingest.transcript.ready.v1            # Transcript completed
ingest.summary.ready.v1               # Summary generated
ingest.chapters.ready.v1              - Chapter markers created
```

### API Gateway Integration

| Service | Gateway URL | Purpose |
|---------|-------------|---------|
| TensorZero | `http://localhost:3030` | LLM routing & observability |
| Hi-RAG v2 | `http://localhost:8086` | Knowledge retrieval |
| Agent Zero | `http://localhost:8080` | MCP API / orchestration |
| Flute-Gateway | `http://localhost:8055` | Voice synthesis |
| Tokenism | `http://localhost:8100` | Economic simulation |

### Shared Storage

| Storage | Purpose | Access |
|---------|---------|--------|
| MinIO | Artifacts, media, analysis results | `pmoves:minio` |
| Supabase | Metadata, content records | API keys |
| Qdrant | Vector embeddings | HTTP API |
| Meilisearch | Full-text search | HTTP API |

---

## Development Patterns

### Service Discovery

Services communicate via Docker service names on internal networks:

```yaml
networks:
  pmoves_api:      # Public ingress
  pmoves_app:      # Business logic
  pmoves_bus:      # NATS messaging
  pmoves_data:     # Databases/storage
  pmoves_monitoring: # Observability
```

### Environment Configuration

Services use tiered environment files for secret segmentation:

```bash
env.tier-llm       # External API keys (highest risk)
env.tier-agent     # Agent coordination
env.tier-worker    # Processing credentials
env.tier-api       # Internal TensorZero
env.tier-data      # Infrastructure only
env.tier-media     # Media processing
```

### Health Checks

All services expose `/healthz` endpoint:

```bash
# Check service health
curl http://localhost:8080/healthz  # Agent Zero
curl http://localhost:8091/healthz  # Archon
curl http://localhost:8100/healthz  # Tokenism
curl http://localhost:8055/healthz  # Flute-Gateway
```

---

## Deployment Patterns

### Standalone Mode

Subsystems can run independently:

```bash
# BoTZ standalone
cd PMOVES-BoTZ
docker compose up -d

# DoX standalone
cd PMOVES-DoX
docker compose up -d
```

### Docked Mode (PMOVES.AI Integration)

Subsystems integrate with main platform:

```bash
# From PMOVES.AI root
docker compose --profile agents up -d           # Agent services
docker compose --profile botz up -d             # BoTZ integration
docker compose --profile media up -d            # Media processing
docker compose --profile orchestration up -d    # Research services
```

### Profile Combinations

| Goal | Profile Combination |
|------|---------------------|
| Full agent stack | `agents,bots,orchestration` |
| Voice processing | `media,tts,gpu` |
| Document pipeline | `media,workers` |
| Economic simulation | `agents,bots` |
| Complete system | All profiles |

---

## Troubleshooting

### Common Issues

**Subsystem can't reach NATS:**
```bash
# Verify NATS is running
docker ps | grep nats

# Check network connectivity
docker network inspect pmoves_bus | grep Subnet
```

**CGP packets not received:**
```bash
# Monitor NATS subjects
nats sub "tokenism.cgp.>" &
nats sub "geometry.>" &
```

**Service health check failing:**
```bash
# Check service logs
docker logs pmoves-tokenism-simulator-1
docker logs pmoves-flute-gateway-1
```

### Debug Commands

```bash
# View all subsystem containers
docker ps --filter "name=pmoves-"

# Check NATS message flow
nats server check
nats stream ls
nats consumer info <stream> <consumer>

# Monitor geometry bus
nats sub "geometry.>" --raw
nats sub "tokenism.cgp.>" --raw
```

---

## References

### Subsystem Documentation
- `/PMOVES-BoTZ/README.md` - BoTZ documentation
- `/PMOVES-DoX/README.md` - DoX documentation (742 lines)
- `/PMOVES-ToKenism-Multi/README.md` - Tokenism documentation

### Integration Guides
- `/.claude/context/geometry-nats-subjects.md` - NATS reference
- `/pmoves/docs/PMOVESCHIT/GEOMETRY_BUS_INTEGRATION.md` - CHIT integration

### API Documentation
- `/PMOVES-DoX/API_REFERENCE.md` - DoX API
- `/.claude/context/flute-gateway.md` - Flute-Gateway API

### Architecture
- `/docs/PMOVES.AI-Edition-Hardened-Full.md` - System architecture
- `/docs/Security-Hardening-Summary-2025-01-29.md` - Security overview
