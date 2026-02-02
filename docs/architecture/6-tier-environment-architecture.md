# 6-Tier Environment Architecture for PMOVES.AI

**Status:** Implemented in Phase 2 Security Hardening (PR #276)
**Last Updated:** 2026-01-29
**Security Score:** 95/100 (Phase 1-2 Complete)

---

## Overview

PMOVES.AI implements **6-tier environment architecture** for secrets management, providing logical isolation at the environment level. This complements the 5-tier network segmentation (physical isolation) to create a **dual-tiered defense-in-depth** security model.

### Key Principle

**Only `env.tier-llm` contains external API keys.** All other services call internal TensorZero.

| Layer | Type | Implementation | Purpose |
|-------|------|----------------|---------|
| **Network Layer** | Physical isolation | 5 Docker bridge networks | Container-to-container communication control |
| **Environment Layer** | Logical isolation | 6 `env.tier-*` files | Secret access segmentation |

---

## Environment Tiers

| Tier | File | Services | Secrets Scope | Blast Radius |
|------|------|----------|---------------|--------------|
| **Data** | `env.tier-data` | postgres, qdrant, neo4j, meilisearch, minio, clickhouse | Infrastructure only, NO API keys | Databases compromised |
| **API** | `env.tier-api` | postgrest, hi-rag-gateway-v2, presign, tensorzero-ui | Data tier + internal TensorZero (NO external keys) | RQ services exposed |
| **Worker** | `env.tier-worker` | extract-worker, langextract, pdf-ingest, notebook-sync | Processing credentials | Workers compromised |
| **Agent** | `env.tier-agent` | agent-zero, archon, mesh-agent, deepresearch | Agent coordination secrets | Agents hijacked |
| **Media** | `env.tier-media` | pmoves-yt, ffmpeg-whisper, media-video, media-audio | Media processing tokens | Media pipeline |
| **LLM** | `env.tier-llm` | **tensorzero-gateway ONLY** | **External LLM API keys** | **HIGHEST RISK** |

---

## Implementation

### Docker Compose Configuration

```yaml
# docker-compose.yml
x-env-tier-data: &env-tier-data
  env_file: [ env.tier-data, .env.local ]

x-env-tier-api: &env-tier-api
  env_file: [ env.tier-api, .env.local ]

x-env-tier-worker: &env-tier-worker
  env_file: [ env.tier-worker, .env.local ]

x-env-tier-agent: &env-tier-agent
  env_file: [ env.tier-agent, .env.local ]

x-env-tier-media: &env-tier-media
  env_file: [ env.tier-media, .env.local ]

x-env-tier-llm: &env-tier-llm
  env_file: [ env.tier-llm, .env.local ]

services:
  # Only service with external LLM keys
  tensorzero-gateway:
    <<: *env-tier-llm
    # ... other config

  # Services that call internal TensorZero
  hi-rag-gateway-v2:
    <<: *env-tier-api
    # Can call http://tensorzero:3000 internally
    environment:
      - TENSORZERO_URL=http://tensorzero:3000

  extract-worker:
    <<: *env-tier-worker
    # NO external LLM access

  agent-zero:
    <<: *env-tier-agent
    # Agent coordination only
```

### Environment File Structure

```
pmoves/
├── env.shared                 # Shared (non-secret) configuration
├── env.tier-data             # Database credentials
├── env.tier-api              # API gateway + internal TensorZero
├── env.tier-worker           # Background processing
├── env.tier-agent            # Agent coordination
├── env.tier-media            # Media pipeline
├── env.tier-llm              # External LLM API keys ⚠️
└── .env.local                # Local overrides (gitignored)
```

### Example: env.tier-llm (HIGH SECURITY)

```bash
# env.tier-llm - ONLY used by tensorzero-gateway
# All other services access LLMs via internal TensorZero

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-xxxxx

# OpenAI
OPENAI_API_KEY=sk-xxxxx

# Google Gemini
GEMINI_API_KEY=xxxxx

# Venice (local fallback)
VENICE_API_KEY=xxxxx

# Ollama (local inference)
OLLAMA_BASE_URL=http://ollama:11434
```

### Example: env.tier-api (NO external keys)

```bash
# env.tier-api - API gateway and services
# These services call internal TensorZero, NOT external providers

# Supabase
SUPABASE_REST_URL=http://postgrest:3010
SUPABASE_ANON_KEY=eyJhbGci...

# Internal TensorZero (NO external keys!)
TENSORZERO_URL=http://tensorzero:3000
TENSORZERO_EMBEDDING_MODEL=gemma_embed_local

# Presign service
PRESIGN_SHARED_SECRET=xxxxx
```

---

## Security Benefits

### 1. Blast Radius Reduction

**Scenario:** Compromised extract-worker (env.tier-worker)

| Attack Vector | env.tier-worker | env.tier-llm |
|---------------|-----------------|--------------|
| External LLM API keys | ❌ Not available | ✅ Available |
| Database credentials | ❌ Not available | ✅ Available |
| Agent coordination tokens | ❌ Not available | ✅ Available |
| Media processing keys | ❌ Not available | ✅ Available |

**Result:** Attacker gets processing credentials ONLY, cannot access LLM API keys or databases.

### 2. Audit Simplicity

Only one file needs external key rotation:

```bash
# Rotate LLM keys (single file)
vi env.tier-llm
# Update: ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.

# Reload tensorzero-gateway only
docker compose restart tensorzero-gateway

# Verify
curl http://localhost:3030/healthz
```

### 3. Secrets Fence via TensorZero

All services route LLM calls through internal TensorZero:

```
┌─────────────────┐
│  Any Service    │
│  (not tier-llm) │
└────────┬────────┘
         │ http://tensorzero:3000
         ↓
┌─────────────────────┐
│  TensorZero Gateway │ ← env.tier-llm
│  (has external keys) │
└─────────────────────┘
         │ https://api.anthropic.com
         ↓
    External LLM Provider
```

**Benefits:**
- Centralized observability (all LLM calls logged)
- Cost tracking (single point of usage)
- Rate limiting and caching
- Easy key rotation

---

## Best Practices

### 1. Never Add External Keys to Non-LLM Tiers

```dockerfile
# ❌ WRONG - External keys in worker
ENV OPENAI_API_KEY=sk-xxxxx

# ✅ CORRECT - Use internal TensorZero
ENV TENSORZERO_URL=http://tensorzero:3000
```

### 2. Validate Tier Assignment in Code Review

When adding new services, validate:

```yaml
# Checklist:
- [ ] Service uses appropriate env.tier-* file
- [ ] Service doesn't directly access external LLM APIs (unless tier-llm)
- [ ] Service calls internal TensorZero if LLM access needed
- [ ] Environment variables match tier purpose
```

### 3. Use Docker Compose YAML Anchors

```yaml
# Reusable tier configuration
x-tier-worker: &tier-worker
  env_file: [ env.tier-worker, .env.local ]
  networks: [app_tier, data_tier, monitoring_tier]

services:
  extract-worker:
    <<: *tier-worker
    # Service-specific config
```

---

## Migration Guide

### Adding a New Service

1. **Determine tier assignment:**
   - Does it need LLM access? → Use env.tier-api (calls TensorZero)
   - Does it process media? → Use env.tier-media
   - Is it an agent? → Use env.tier-agent
   - Does it process data? → Use env.tier-worker
   - Is it a database? → Use env.tier-data
   - Is it TensorZero itself? → Use env.tier-llm

2. **Add to docker-compose.yml:**
   ```yaml
   new-service:
     <<: *tier-worker  # Or appropriate tier
     networks: [app_tier, monitoring_tier]
   ```

3. **Create/update environment file:**
   ```bash
   # env.tier-worker
   NEW_SERVICE_VAR=value
   ```

### Migrating from Flat .env

**Before (single .env file):**
```bash
# .env (all secrets in one file)
ANTHROPIC_API_KEY=sk-xxxxx
SUPABASE_DB_PASSWORD=xxxxx
EXTRACT_WORKER_TOKEN=xxxxx
```

**After (6-tier separation):**
```bash
# env.tier-llm
ANTHROPIC_API_KEY=sk-xxxxx

# env.tier-data
POSTGRES_PASSWORD=xxxxx

# env.tier-worker
EXTRACT_WORKER_TOKEN=xxxxx
```

---

## Validation

### Test Tier Isolation

```bash
# Test 1: Worker cannot access external LLM (should fail)
docker compose exec -T extract-worker \
  curl -I https://api.anthropic.com
# Expected: Connection refused or timeout

# Test 2: Worker CAN access internal TensorZero (should succeed)
docker compose exec -T extract-worker \
  curl http://tensorzero:3000/healthz
# Expected: 200 OK

# Test 3: TensorZero CAN access external LLM (should succeed)
docker compose exec -T tensorzero-gateway \
  curl -I https://api.anthropic.com
# Expected: 200 OK (has ANTHROPIC_API_KEY)
```

### Verify Environment Variables

```bash
# Check which env files service loads
docker compose config | grep -A 10 "extract-worker:"
# Should show: env_file: [ env.tier-worker, .env.local ]

# Verify loaded variables
docker compose exec -T extract-worker env | grep -E "(TENSORZERO|OPENAI)"
# Should see: TENSORZERO_URL=http://tensorzero:3000
# Should NOT see: OPENAI_API_KEY
```

---

## Related Documentation

- [Network Tier Segmentation](network-tier-segmentation.md) - Physical network isolation
- [PMOVES.AI-Edition-Hardened-Full](../PMOVES.AI-Edition-Hardened-Full.md) - Complete security documentation
- [Security Hardening Roadmap](../Security-Hardening-Roadmap.md) - Phase 3 initiatives

---

## Summary

The 6-tier environment architecture provides **logical secret isolation** that complements physical network isolation:

1. **Each tier has minimal secrets** for its function
2. **Only tier-llm has external API keys**
3. **TensorZero acts as secrets fence** for all LLM access
4. **Blast radius is minimized** - compromised service affects only its tier
5. **Audit and rotation are simplified** - single file per tier

**Together with 5-tier network segmentation, this creates a defense-in-depth architecture where a compromised service faces TWO barriers: network isolation AND secret isolation.**
