# Tier-Based Credential System

**Purpose:** Document PMOVES.AI's tier-based credential architecture for secret management.

**Last Updated:** 2026-02-12

---

## Overview

PMOVES.AI uses a **tier-based credential system** to organize environment variables by service type. Each tier has its own environment file that is loaded based on the service's tier classification.

```
┌─────────────────────────────────────────────────────────────────┐
│              PMOVES.AI Parent Repository                   │
├─────────────────────────────────────────────────────────────────┤
│        Tier-Based Environment Files                    │
│     ┌───────────────────────────────────────────┐   │
│     │ env.shared (base - all tiers)       │   │
│     ├─────────────────────────────────────────┤   │
│     │ env.tier-llm (LLM services)      │   │
│     │ env.tier-data (databases)          │   │
│     │ env.tier-api (gateways)           │   │
│     │ env.tier-agent (orchestration)     │   │
│     │ env.tier-worker (background)        │   │
│     │ env.tier-media (media processing)   │   │
│     └─────────────────────────────────────────┘   │
│                                             ▼         │
└───────────────────────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│         Bootstrap Script (bootstrap_credentials.sh)  │
│     - Detects DOCKED_MODE                   │
│     - Loads appropriate tier files              │
│     - Merges with common credentials           │
│     - Creates .env.bootstrap for runtime        │
└───────────────────────────────────────────────────────┘
```

---

## Tier Classification

| Tier | Description | Example Services | Env File |
|-------|-------------|-------------------|-----------|
| **llm** | LLM Gateway services | TensorZero | `env.tier-llm` |
| **data** | Database and storage services | Qdrant, Neo4j, Meilisearch | `env.tier-data` |
| **api** | Gateway and API services | Archon, HiRAG | `env.tier-api` |
| **agent** | Agent orchestration services | Agent Zero, BoTZ | `env.tier-agent` |
| **worker** | Background processing services | Extract Worker, LangExtract | `env.tier-worker` |
| **media** | Media processing services | Ultimate-TTS-Studio, Pipecat | `env.tier-media` |

---

## Environment File Structure

### env.shared (Base Credentials)

**Location:** `pmoves/env.shared`

**Purpose:** Common credentials shared across all services

**Contents:**
```bash
# PMOVES.AI Shared Environment Variables
# These are loaded for ALL services regardless of tier

# Infrastructure
NATS_URL=nats://nats:4222
TENSORZERO_URL=http://tensorzero:3030

# Service names (for service discovery)
AGENT_ZERO_URL=http://agent-zero:8080
ARCHON_URL=http://archon:8091
HIRAG_V2_URL=http://hi-rag-gateway-v2:8086

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Mode detection
CHIT_ENVIRONMENT=production
DOCKED_MODE=false
```

### env.tier-llm (LLM Provider Keys)

**Purpose:** LLM provider API keys for TensorZero gateway

**Contents:**
```bash
# LLM Provider Credentials
# These are ONLY available to LLM tier services

# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Google
GOOGLE_API_KEY=...

# Other providers
VENICE_API_KEY=...
OPENROUTER_API_KEY=...
```

### env.tier-data (Database Credentials)

**Purpose:** Database connection credentials for data tier services

**Contents:**
```bash
# Database Credentials

# Qdrant (vector database)
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=...

# Neo4j (graph database)
NEO4J_URL=http://neo4j:7474
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...

# Meilisearch (full-text search)
MEILISEARCH_URL=http://meilisearch:7700
MEILISEARCH_MASTER_KEY=...

# SurrealDB
SURREAL_URL=http://surrealdb:8000
SURREAL_USER=root
SURREAL_PASSWORD=...
SURREAL_NS=pmoves
SURREAL_DB=pmoves
```

### env.tier-api (Gateway Services)

**Purpose:** Credentials for API gateway services

**Contents:**
```bash
# API Gateway Credentials

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=...

# External APIs (if service uses them)
EXTERNAL_SERVICE_API_KEY=...
```

### env.tier-agent (Agent Services)

**Purpose:** Credentials for agent orchestration services

**Contents:**
```bash
# Agent Service Credentials

# Agent provider access
AGENT_PROVIDER_URL=...

# Tool access
TOOL_API_KEY=...
```

### env.tier-worker (Background Workers)

**Purpose:** Credentials for background worker services

**Contents:**
```bash
# Worker Service Credentials

# Processing configuration
WORKER_CONCURRENCY=4
WORKER_TIMEOUT=300

# Storage access for results
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
```

### env.tier-media (Media Services)

**Purpose:** Credentials for media processing services

**Contents:**
```bash
# Media Processing Credentials

# YouTube (for PMOVES.YT)
YOUTUBE_API_KEY=...

# Whisper (for transcription)
WHISPER_MODEL=small

# TTS providers
ELEVENLABS_API_KEY=...
```

---

## Bootstrap Process

**Location:** `pmoves/scripts/bootstrap_credentials.sh`

### Execution Flow

```
┌─────────────────────────────┐
│ 1. Detect Mode           │
│    - Check DOCKED_MODE     │
│    - Check /.dockerenv     │
└───────────┬───────────────┘
            │
            ▼
┌─────────────────────────────┐
│ 2. Determine Tier        │
│    - Read SERVICE_TIER    │
│    - Or use default       │
└───────────┬───────────────┘
            │
            ▼
┌─────────────────────────────┐
│ 3. Load Tier File        │
│    - Source env.tier-*    │
└───────────┬───────────────┘
            │
            ▼
┌─────────────────────────────┐
│ 4. Load Common          │
│    - Source env.shared    │
└───────────┬───────────────┘
            │
            ▼
┌─────────────────────────────┐
│ 5. Merge & Export       │
│    - Combine all vars    │
│    - Create .env.bootstrap│
└───────────────────────────┘
```

### Mode Detection

```bash
# From bootstrap_credentials.sh

# Detect docked mode
if [[ -f /.dockerenv ]]; then
    MODE="docked"
    export DOCKED_MODE=true
else
    MODE="standalone"
    export DOCKED_MODE=false
fi

echo "Detected mode: $MODE"
```

### Tier Loading

```bash
# Determine service tier
SERVICE_TIER=${SERVICE_TIER:-"api"}

# Load tier-specific file
case "$SERVICE_TIER" in
    llm)
        if [[ -f env.tier-llm ]]; then
            source env.tier-llm
        fi
        ;;
    data)
        if [[ -f env.tier-data ]]; then
            source env.tier-data
        fi
        ;;
    api)
        if [[ -f env.tier-api ]]; then
            source env.tier-api
        fi
        ;;
    agent)
        if [[ -f env.tier-agent ]]; then
            source env.tier-agent
        fi
        ;;
    worker)
        if [[ -f env.tier-worker ]]; then
            source env.tier-worker
        fi
        ;;
    media)
        if [[ -f env.tier-media ]]; then
            source env.tier-media
        fi
        ;;
esac

# Load common credentials
if [[ -f env.shared ]]; then
    source env.shared
fi
```

### Export to Runtime

```bash
# Export all variables for runtime
export > .env.bootstrap
```

---

## Adding New Credentials

### 1. Determine Tier

Which tier does your service belong to?
- `llm` - Uses LLM provider APIs
- `data` - Connects to databases
- `api` - Gateway/API service
- `agent` - Agent orchestration
- `worker` - Background processing
- `media` - Media processing

### 2. Add to Tier File

Add your credential to the appropriate tier file:

```bash
# Example: Adding to env.tier-api
MY_SERVICE_API_KEY=your-api-key-here
MY_SERVICE_URL=https://api.service.com
```

### 3. Update env.shared (if common)

If the credential is used by multiple services, add to `env.shared`:

```bash
# Common service URL used by multiple services
MY_COMMON_SERVICE_URL=http://common-service:8080
```

### 4. Update Service Manifest

Add to your service's `chit/secrets_manifest_v2.yaml`:

```yaml
secrets:
  - name: MY_SERVICE_API_KEY
    description: "API key for MyService"
    required: true
    category: credentials
    source: env
```

---

## Security Considerations

### LLM Tier Isolation

**Critical:** LLM tier is the ONLY tier that should have access to external LLM provider API keys.

- All other services call TensorZero internally
- TensorZero manages provider keys
- Services never touch provider keys directly

### Credential Precedence

When credentials are defined in multiple files:

1. **env.tier-*` - Highest precedence (tier-specific)
2. **env.shared** - Lower precedence (fallback)
3. **.env** - Local overrides (development only)

### Secret Synchronization

The bootstrap script:
1. Detects mode (docked vs standalone)
2. Loads appropriate tier files
3. Merges with common credentials
4. Creates runtime environment

---

## Troubleshooting

### Credentials Not Loading

1. Check `SERVICE_TIER` is set correctly
2. Verify tier file exists (`env.tier-*`)
3. Check bootstrap script is running
4. Verify `.env.bootstrap` is created

### Wrong Credentials Being Used

1. Check credential precedence order
2. Verify tier file is loaded after `env.shared`
3. Check for conflicting variable names

### Secrets Not Available in Container

1. Verify secrets are passed to container
2. Check `docker-compose.yml` environment section
3. Verify CHIT v2 manifest is correct

---

## Related Documentation

- [CHIT_V2_SPECIFICATION.md](CHIT_V2_SPECIFICATION.md) - CHIT manifest format
- [PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md](PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md) - Integration guide
- [SECRETS_ONBOARDING.md](SECRETS_ONBOARDING.md) - Secret onboarding

---

**Maintainer:** PMOVES.AI Team
