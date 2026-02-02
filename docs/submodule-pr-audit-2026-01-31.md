# Submodule PR Audit Report

**Date:** 2026-01-31
**Branch:** PMOVES.AI-Edition-Hardened
**Total Submodules Audited:** 34
**Open PRs Found:** 2

---

## Executive Summary

Two open pull requests require attention for PMOVES.AI integration:

| PR | Repository | Status | CI | Docstrings | Issues |
|----|------------|--------|----|-----------|--------|
| #2 | PMOVES-BotZ-gateway | OPEN | ✅ Pass | ⚠️ 74% | 12 actionable |
| #2 | PMOVES-Archon | OPEN | ✅ Pass | ✅ 96.55% | 6 actionable |

**Both PRs add PMOVES.AI integration patterns but have issues that should be addressed before merge.**

---

## PR #1: PMOVES-BotZ-gateway #2

**Title:** feat: Add PMOVES.AI integration patterns
**Branch:** `feat/pmoves-ai-integration` → `main`
**Size:** 1398 additions across 8 files
**Created:** 2026-01-20
**Author:** POWERFULMOVES

### CI Status
- GitHub Actions: ✅ Pass
- Docstring Coverage: ⚠️ 74% (threshold: 80%)
- Pre-merge checks: 2 passed, 1 warning

### Files Added
| File | Purpose |
|------|---------|
| `PMOVES.AI_INTEGRATION.md` | Integration guide |
| `env.shared` | Base environment configuration |
| `env.tier-api` | API tier configuration |
| `chit/secrets_manifest_v2.yaml` | CHIT secrets template |
| `pmoves_announcer/__init__.py` | NATS service announcer |
| `pmoves_health/__init__.py` | Health check framework |
| `pmoves_registry/__init__.py` | Service registry client |
| `docker-compose.pmoves.yml` | Docker Compose anchors |

### CodeRabbit Issues (12 Actionable)

#### Security Issues (Must Fix)
1. **Insecure Neo4j default password** (`env.shared:50-53`)
   - Hardcoded `NEO4J_PASSWORD=neo4j` default
   - Fix: Remove default, require explicit value

2. **Insecure MinIO credentials** (`env.shared:59-62`)
   - `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` default to `minioadmin`
   - Fix: Remove defaults, require explicit values

3. **Overly permissive CORS** (`env.tier-api:21-25`)
   - `CORS_ORIGINS=*` with credentials enabled
   - Fix: Default to restricted origins, disable credentials

#### Missing Files (Must Fix)
4. **Docker Compose references missing env files** (`docker-compose.pmoves.yml:38-98`)
   - Anchors reference `env.tier-agent`, `env.tier-worker`, `env.tier-data`, `env.tier-llm`, `env.tier-media`
   - These files don't exist in the PR
   - Fix: Create stub files or mark optional

#### Documentation Issues (Should Fix)
5. **Wrong filename in comment** (`env.tier-api:1-9`)
   - Comment mentions `env.tier-api.sh` but file is `env.tier-api`

6. **Wrong module import examples** (`pmoves_announcer/__init__.py:1-30`)
   - Examples show importing from `service_announcer` instead of `pmoves_announcer`

7. **Module docstring mismatch** (`pmoves_registry/__init__.py:1-19`)
   - Claims resolution chain includes Supabase/NATS but only implements env + DNS

#### Code Quality Issues (Should Fix)
8. **Decorator duplicate registration** (`pmoves_health/__init__.py:188-199`)
   - `health_check` decorator adds checks on every invocation
   - Fix: Move registration to decorator closure

9. **Missing health endpoint in DNS fallback** (`pmoves_registry/__init__.py:125-168`)
   - Fallback URL doesn't append `/health` for health checks
   - Fix: Append health path to fallback URL

10. **Incorrect return type** (`pmoves_registry/__init__.py:224-254`)
    - `CommonServices.get` declares `str` return but may return `None`
    - Fix: Change to `Optional[str]`

#### Style Issues (Nice to Have)
11. **Bare URL in markdown** (`PMOVES.AI_INTEGRATION.md:71-78`)
    - markdownlint MD034 violation

### Recommendation

**Status:** ⚠️ Needs revision before merge

**Required actions:**
1. Fix security issues (insecure defaults)
2. Create missing env files or update Docker Compose template
3. Fix docstring coverage (add missing docstrings)
4. Address code quality issues

**Merge target:** Should merge to `PMOVES.AI-Edition-Hardened` branch instead of `main`

---

## PR #2: PMOVES-Archon #2

**Title:** feat(archon): add persona service and API routes for agent creation
**Branch:** `feat/personas-first-architecture` → `PMOVES.AI-Edition-Hardened`
**Size:** 1213 additions
**Created:** 2026-01-15
**Author:** POWERFULMOVES

### CI Status
- GitHub Actions: ✅ Pass
- Docstring Coverage: ✅ 96.55% (threshold: 80%)
- Pre-merge checks: 3 passed

### Files Added
| Category | Files |
|----------|-------|
| Infrastructure | `.github/CODEOWNERS`, `.github/dependabot.yml`, `.gitmodules` |
| Submodules | 7 new submodules (Agent-Zero, BoTZ, HiRAG, Deep-Serch, etc.) |
| MCP Adapter | `python/pmoves_mcp/__init__.py`, `python/pmoves_mcp/claude_code_adapter.py` |
| Persona Service | `python/src/server/services/persona_service.py` |
| Persona API | `python/src/server/api_routes/persona_api.py` |
| Metrics | Updates to `python/src/server/main.py`, `python/pyproject.toml` |

### CodeRabbit Issues (6 Actionable)

#### Configuration Issues (Must Fix)
1. **Dependabot directory paths wrong** (`.github/dependabot.yml:1-20`)
   - All entries point to `"/"` instead of actual manifest locations
   - Fix: Point `pip` to `/python`, `npm` to `/archon-ui-main` and `/docs`

2. **Missing dependency group** (`python/pyproject.toml:67-68`)
   - `prometheus-client` not in `dependency-groups.all`
   - Fix: Add `prometheus-client>=0.20.0` to `all` group

#### Submodule Issues (Must Fix)
3. **Agent Zero submodule not integrated** (`external/PMOVES-Agent-Zero`)
   - Submodule added but never used in code
   - Fix: Implement integration or remove submodule

4. **BoTZ submodule broken reference** (`external/PMOVES-BoTZ`)
   - Pinned to non-existent commit `b39e3b4bf3974296e1d78f469ff1d0ae19ed551b`
   - Fix: Update to valid commit on `PMOVES.AI-Edition-Hardened`

5. **Docling submodule missing branch** (`pmoves_multi_agent_pro_pack/docling`)
   - `.gitmodules` entry missing `branch = PMOVES.AI-Edition-Hardened`
   - Fix: Add branch specification

#### Code Quality Issues (Should Fix)
6. **Async function with blocking Supabase call** (`python/src/server/services/persona_service.py:108-148`)
   - `get_persona` is async but calls synchronous Supabase client
   - Fix: Wrap in `asyncio.to_thread` or make synchronous

### Nitpicks (11 items)
- Expand CODEOWNERS Dockerfile pattern to `*Dockerfile*`
- Move source directories out of repo root
- Clarify submodule usage in PR description

### Recommendation

**Status:** ⚠️ Needs revision before merge

**Required actions:**
1. Fix Dependabot directory paths
2. Fix BoTZ submodule reference
3. Add missing prometheus-client to dependency group
4. Either implement Agent Zero integration or remove submodule
5. Fix async/sync mismatch in persona service

**Merge target:** ✅ Correctly targets `PMOVES.AI-Edition-Hardened`

---

## Cross-Cutting Concerns

### Branch Naming
Both PRs use feature branches that should be merged to `PMOVES.AI-Edition-Hardened`:
- BotZ-gateway PR #2 targets `main` (should target `PMOVES.AI-Edition-Hardened`)
- Archon PR #2 correctly targets `PMOVES.AI-Edition-Hardened`

### Integration Pattern Compliance
Both PRs follow the PMOVES.AI integration template:
- ✅ CHIT secrets manifest
- ✅ Tier-based env loading
- ✅ NATS service discovery
- ✅ Health endpoints
- ✅ Service registry

### Docstring Standards
- BotZ-gateway: 74% (below 80% threshold)
- Archon: 96.55% (exceeds threshold)

---

## Submodule Status Summary

From the concurrent submodule audit, these submodules have uncommitted changes:

| Submodule | Branch | Issue | Action |
|-----------|--------|-------|--------|
| PMOVES-DoX | feat/ci-ui-smoke-fix-auth-hardening | Feature branch | Merge to Hardened |
| PMOVES-Open-Notebook | fix/api-file-path-initialization | Fix branch | Merge to Hardened |
| PMOVES-Wealth | v6.4.4-6-g55ea3c3af9 | Ahead of tag | Sync to Hardened |
| PMOVES-transcribe-and-fetch | Not initialized | Missing | `git submodule update --init` |

---

## Next Steps

### Immediate (Before Merge)
1. **PMOVES-BotZ-gateway PR #2**
   - Address 12 CodeRabbit issues
   - Fix docstring coverage (74% → 80%+)
   - Change target branch to `PMOVES.AI-Edition-Hardened`

2. **PMOVES-Archon PR #2**
   - Address 6 CodeRabbit issues
   - Fix submodule references
   - Fix dependency declaration

### After PRs Merge
3. Initialize PMOVES-transcribe-and-fetch submodule
4. Sync DoX, Open-Notebook, and Wealth to PMOVES.AI-Edition-Hardened

### Documentation
5. Update integration template to address common issues found in review
6. Add PR review checklist to PMOVES.AI integration guide

---

## References

- PMOVES-BotZ-gateway PR #2: https://github.com/POWERFULMOVES/PMOVES-BotZ-gateway/pull/2
- PMOVES-Archon PR #2: https://github.com/POWERFULMOVES/PMOVES-Archon/pull/2
- Submodule Audit: `/docs/submodule-audit-2026-01-31.md`
- Phase 2 Plan: `/docs/phase2-security-hardening-plan.md`
