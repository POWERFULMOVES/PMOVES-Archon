# PMOVES.AI Submodule Catalog

**Purpose:** Complete catalog of all PMOVES.AI submodules with their purposes, ports, and integration status.

**Last Updated:** 2026-02-12

---

## Quick Reference

| Category | Count | Submodules |
|-----------|--------|-------------|
| **Agent Orchestration** | 4 | Agent-Zero, Archon, BoTZ, BotZ-gateway |
| **Knowledge & Research** | 4 | A2UI, HiRAG, Deep-Serch, hyperdimensions |
| **Agent Training** | 4 | AgentGym, Gym-RL, llama-lab, surf |
| **E2B Sandbox** | 6 | Danger-Room, Danger-Room-Desktop, Danger-infra, e2b-mcp-server, E2b-Spells |
| **Voice & Speech** | 4 | Pipecat, Ultimate-TTS-Studio, Pinokio-TTS, transcribe-and-fetch |
| **Media & Content** | 3 | PMOVES.YT, Jellyfin, Jellyfin-AI-Media-Stack |
| **Document Processing** | 2 | DoX, Creator |
| **Knowledge Base** | 2 | Open-Notebook (x2 variants) |
| **Workflow & Automation** | 2 | n8n, crush |
| **LLM Gateway** | 1 | TensorZero |
| **Financial** | 3 | Wealth, Firefly-iii, Health-wger |
| **Networking** | 4 | Tailscale, Remote-View, Headscale, surf |
| **Data Storage** | 1 | Tokenism-Multi |
| **Integrations** | 2 | archon (nested), Supabase |
| **UI** | 1 | MAI-UI |

**Total:** 41 submodules

---

## How to Add a New Submodule

### Step 1: Fork the Repository

```bash
# Fork the upstream repository to POWERFULMOVES organization
gh repo fork upstream-user/upstream-repo --org POWERFULMOVES
```

### Step 2: Add to .gitmodules

Add entry to `.gitmodules` in the appropriate category section:

```gitmodules
[submodule "PMOVES-NewService"]
	path = PMOVES-NewService
	url = https://github.com/POWERFULMOVES/PMOVES-NewService.git
	branch = PMOVES.AI-Edition-Hardened
```

**Key Pattern Rules:**
1. **Path naming:** Use `PMOVES-*` prefix for consistency
2. **URL format:** `https://github.com/POWERFULMOVES/PMOVES-ServiceName.git`
3. **Branch:** Always `PMOVES.AI-Edition-Hardened` (or variant for nested)
4. **Tab character:** Use literal tab (`	`) before `branch`, not spaces

### Step 3: Initialize the Submodule

```bash
# Add and clone the submodule
git submodule add -b PMOVES.AI-Edition-Hardened \
  https://github.com/POWERFULMOVES/PMOVES-NewService.git \
  PMOVES-NewService

# Verify branch
cd PMOVES-NewService
git branch --show-current  # Should be: PMOVES.AI-Edition-Hardened
```

### Step 4: Create Integration Files

Inside the new submodule, create these integration files:

1. **`chit/secrets_manifest_v2.yaml`** - Service metadata for CHIT v2
   - Copy template from `pmoves/templates/submodule/chit/secrets_manifest_v2.yaml`
   - Define service slug, ports, and required secrets

2. **`PMOVES.AI_INTEGRATION.md`** - Integration documentation
   - Describe service purpose and PMOVES.AI integration points
   - Document required environment variables
   - List health endpoints and NATS subjects

3. **`env.shared`** (if needed) - Add service credentials
   - Follow `{{SERVICE_NAME}}_API_KEY` pattern
   - Include in parent `pmoves/env.shared`

### Step 5: Update Parent Repository Files

1. **`pmoves/docker-compose.pmoves.yml`** - Add service definition with anchors
2. **`pmoves/env.shared`** - Add service credential templates
3. **`pmoves/chit/secrets_manifest_v2.yaml`** - Register service secrets
4. **This catalog** (`SUBMODULE_LIST.md`) - Add entry below

---

## Submodule Catalog

### Agent Orchestration Services

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **Agent-Zero** | `PMOVES-Agent-Zero` | PMOVES.AI-Edition-Hardened | Primary orchestrator with MCP API | `:8080/healthz` |
| **Archon** | `PMOVES-Archon` | PMOVES.AI-Edition-Hardened | Supabase-driven agent service with prompt/form management | `:8091/healthz` |
| **BoTZ** | `PMOVES-BoTZ` | PMOVES.AI-Edition-Hardened | Multi-agent MCP platform with security hooks | `:8081/healthz` |
| **BotZ-gateway** | `PMOVES-BotZ-gateway` | PMOVES.AI-Edition-Hardened | MCP Gateway aggregation for BoTZ ecosystem | `:3020/health` |

### Knowledge & Research Services

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **A2UI** | `PMOVES-A2UI` | PMOVES.AI-Edition-Hardened | UI for research/knowledge services | `:3000/healthz` |
| **HiRAG** | `PMOVES-HiRAG` | PMOVES.AI-Edition-Hardened | Hybrid RAG (vector + graph + full-text) | `:8086/healthz` |
| **Deep-Serch** | `PMOVES-Deep-Serch` | PMOVES.AI-Edition-Hardened | LLM-based research planner | `:8098/healthz` |
| **hyperdimensions** | `Pmoves-hyperdimensions` | PMOVES.AI-Edition-Hardened | Mathematical visualization | `:4200/healthz` |

### Agent Training & Research Platforms

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **AgentGym** | `PMOVES-AgentGym` | PMOVES.AI-Edition-Hardened | Agent training environment | `:5000/healthz` |
| **AgentGym-RL** | `Pmoves-AgentGym-RL` | PMOVES.AI-Edition-Hardened | RL agent training | `:5001/healthz` |
| **llama-lab** | `PMOVES-llama-throughput-lab` | PMOVES.AI-Edition-Hardened | LLaMA throughput testing | `:5002/healthz` |
| **surf** | `PMOVES-surf` | PMOVES.AI-Edition-Hardened | Web crawling framework | `:5003/healthz` |

### E2B Sandbox Services

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **Danger-Room** | `PMOVES-E2B-Danger-Room` | PMOVES.AI-Edition-Hardened | Secure Python/JavaScript execution | `:7071/health` |
| **Danger-Room-Desktop** | `PMOVES-E2B-Danger-Room-Desktop` | PMOVES.AI-Edition-Hardened | Desktop sandbox execution | `:7070/health` |
| **Danger-infra** | `PMOVES-Danger-infra` | PMOVES.AI-Edition-Hardened | E2B infrastructure | `:7069/health` |
| **e2b-mcp-server** | `pmoves-e2b-mcp-server` | PMOVES.AI-Edition-Hardened | E2B MCP server | `:7071/health` |
| **E2b-Spells** | `PMOVES-E2b-Spells` | PMOVES.AI-Edition-Hardened | E2B spell execution framework | `:7068/health` |

**Note:** Former vendor entries were migrated to forked submodules on 2026-02-07. See `.gitmodules` for commented legacy entries.

### Voice & Speech Services

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **Pipecat** | `PMOVES-Pipecat` | PMOVES.AI-Edition-Hardened | Multimodal voice communication framework | `:8055/healthz` |
| **Ultimate-TTS-Studio** | `PMOVES-Ultimate-TTS-Studio` | PMOVES.AI-Edition-Hardened | Multi-engine TTS with 7 engines | `:7861/healthz` |
| **Pinokio-TTS** | `PMOVES-Pinokio-Ultimate-TTS-Studio` | PMOVES.AI-Edition-Hardened | Pinokio TTS integration | `:7862/healthz` |
| **transcribe-and-fetch** | `PMOVES-transcribe-and-fetch` | PMOVES.AI-Edition-Hardened | Audio transcription and media fetching | `:8078/healthz` |

### Media & Content Services

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **PMOVES.YT** | `PMOVES.YT` | PMOVES.AI-Edition-Hardened | YouTube ingestion and processing | `:8077/healthz` |
| **Jellyfin** | `PMOVES-Jellyfin` | PMOVES.AI-Edition-Hardened | Media server integration | `:8092/healthz` |
| **Jellyfin-AI-Media-Stack** | `Pmoves-Jellyfin-AI-Media-Stack` | PMOVES.AI-Edition-Hardened | AI-powered media processing | `:8093/healthz` |

### Knowledge Base Services

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **Open-Notebook** | `PMOVES-Open-Notebook` | PMOVES.AI-Edition-Hardened | Alternative to NotebookLM, SurrealDB backend | `:5055/healthz` |
| **open-notebook** | `Pmoves-open-notebook` | PMOVES.AI-Edition-Hardened | Integration workspace variant | `:5056/healthz` |

### Document Processing Services

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **DoX** | `PMOVES-DoX` | PMOVES.AI-Edition-Hardened | Document intelligence with nested submodules | `:8094/healthz` |
| **Creator** | `PMOVES-Creator` | PMOVES.AI-Edition-Hardened | Content creation tools | `:8095/healthz` |

### Workflow & Automation Services

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **n8n** | `PMOVES-n8n` | PMOVES.AI-Edition-Hardened | Workflow automation platform | `:5678/healthz` |
| **crush** | `PMOVES-crush` | PMOVES.AI-Edition-Hardened | Data processing CLI | N/A |

### LLM Gateway Services

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **TensorZero** | `PMOVES-tensorzero` | PMOVES.AI-Edition-Hardened | Centralized LLM gateway with observability | `:3030/healthz` |

### Financial Services

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **Wealth** | `PMOVES-Wealth` | PMOVES.AI-Edition-Hardened | Financial tracking and management | `:8100/healthz` |
| **Firefly-iii** | `PMOVES-Firefly-iii` | PMOVES.AI-Edition-Hardened | Personal finance manager | `:8101/healthz` |
| **Health-wger** | `Pmoves-Health-wger` | PMOVES.AI-Edition-Hardened | Health tracking | `:8102/healthz` |

### UI Services

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **MAI-UI** | `PMOVES-MAI-UI` | PMOVES.AI-Edition-Hardened | Multimodal AI UI | `:3001/healthz` |

### Networking Services

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **Tailscale** | `PMOVES-Tailscale` | PMOVES.AI-Edition-Hardened | VPN integration | `:41641/healthz` |
| **Remote-View** | `PMOVES-Remote-View` | PMOVES.AI-Edition-Hardened | Remote viewing capabilities | `:8103/healthz` |
| **Headscale** | `PMOVES-Headscale` | PMOVES.AI-Edition-Hardened | Headscale coordination server | `:8099/healthz` |

### Data Storage Services

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **Tokenism-Multi** | `PMOVES-ToKenism-Multi` | PMOVES.AI-Edition-Hardened | Multi-agent Tokenism math system | `:4201/healthz` |

### Integration Services

| Submodule | Path | Branch | Purpose | Health Endpoint |
|-----------|------|--------|---------|-----------------|
| **archon (nested)** | `pmoves/integrations/archon` | PMOVES.AI-Edition-Hardened | Archon integration copy | `:8091/healthz` |
| **Supabase** | `PMOVES-supabase` | PMOVES.AI-Edition-Hardened | Supabase local deployment | `:3010/healthz` |

---

## Nested Submodules

### PMOVES-DoX Nested Submodules

PMOVES-DoX contains its own nested submodules for specialized functionality:

| Nested Submodule | Branch | Purpose |
|-----------------|--------|---------|
| `A2UI_reference` | PMOVES.AI-Edition-Hardened | A2UI reference implementation |
| `PsyFeR_reference` | main | Cipher memory reference |
| `external/Pmoves-Glancer` | PMOVES.AI-Edition-Hardened | Data glancer |
| `external/hyperdimensions` | PMOVES.AI-Edition-Hardened | Math visualization |
| `external/conductor` | v0.1.1 | Google Conductor |
| `external/PMOVES-Agent-Zero` | PMOVES.AI-Edition-Hardened-DoX | Agent Zero (DoX variant) |
| `external/PMOVES-BoTZ` | PMOVES.AI-Edition-Hardened | BoTZ integration |
| `external/BotZ-gateway` | main | BoTZ gateway |

**Note:** `PMOVES.AI-Edition-Hardened-DoX` is a variant branch for nested Agent Zero submodule.

---

## Branch Strategy

All submodules follow this branch strategy:

1. **Primary Branch:** `PMOVES.AI-Edition-Hardened`
2. **Production Branch:** `PMOVES.AI-Edition-Hardened` is the production target
3. **Development Branch:** Feature branches off `main`
4. **Variant Branches:** Use suffix for specialized forks (e.g., `-DoX`, `-Archon`)

### Sync Workflow

```bash
# 1. In submodule: merge main to hardened
git checkout PMOVES.AI-Edition-Hardened
git merge main
git push

# 2. In parent repo: update submodule reference
git add PMOVES-NewService
git commit -m "chore(submodules): Update PMOVES-NewService to latest hardened"
git push
```

---

## Port Registry

See `pmoves/docs/PORT_REGISTRY.md` for complete port assignments.

Quick reference:
- **Agent Services:** 8080-8099
- **Knowledge/Search:** 8086-8099
- **Media Processing:** 8077-8083
- **TTS/Voice:** 7860-7862, 8055-8056
- **Infrastructure:** 3000-3030 (UIs), 4000-4164 (observability)

---

## Related Documentation

- [PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md](PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md) - Detailed integration guide
- [SUBMODULE_ARCHITECTURE.md](SUBMODULE_ARCHITECTURE.md) - Architecture and docking patterns
- [PORT_REGISTRY.md](PORT_REGISTRY.md) - Complete port assignments
- [SUBMODULE_COMMIT_REVIEW_2026-02-07.md](SUBMODULE_COMMIT_REVIEW_2026-02-07.md) - Commit alignment status

---

**Maintainer:** PMOVES.AI Team
**For questions:** See `pmoves/docs/README_DOCS_INDEX.md` for documentation index
