# PMOVES.AI Documentation Update Plan

**Created:** 2026-01-29
**Status:** In Progress
**Objective:** Comprehensive documentation refresh for PMOVES.AI-Edition-Hardened

---

## Overview

This plan addresses the need to update core PMOVES.AI documentation to reflect:
1. **6-Tier Environment Architecture** (env.tier-* secret segmentation)
2. **5-Tier Network Segmentation** (Docker network isolation)
3. **Latest GitHub and Docker official documentation**
4. **Proper namespace publishing** (GHCR lowercase normalization)
5. **Tailscale VPN configuration** for production access
6. **New submodules** added during audit
7. **Docker hardening best practices** (USER directives, multi-stage builds)

---

## Architecture Clarification

PMOVES.AI implements **dual-tiered security**:

### 1. Network Tier Segmentation (5 Docker Networks)
| Tier | Network | Subnet | Services | Purpose |
|------|---------|--------|----------|---------|
| API | `pmoves_api` | 172.30.1.0/24 | 16 services | Public ingress |
| Application | `pmoves_app` | 172.30.2.0/24 | 19 services | Business logic |
| Bus | `pmoves_bus` | 172.30.3.0/24 | 1 service | NATS messaging |
| Data | `pmoves_data` | 172.30.4.0/24 | 7 services | Databases/storage |
| Monitoring | `pmoves_monitoring` | 172.30.5.0/24 | 5 services | Observability |

### 2. Environment Tier Architecture (6 Secret Segments)
| Tier | File | Secrets Scope | Blast Radius |
|------|------|---------------|--------------|
| Data | `env.tier-data` | Infrastructure only | Databases compromised |
| API | `env.tier-api` | Internal TensorZero | RQ services exposed |
| Worker | `env.tier-worker` | Processing credentials | Workers compromised |
| Agent | `env.tier-agent` | Agent coordination | Agents hijacked |
| Media | `env.tier-media` | Media processing | Media pipeline |
| LLM | `env.tier-llm` | **External API keys** | **HIGHEST RISK** |

**Key Principle:** Only `env.tier-llm` contains external API keys. All other services call internal TensorZero.

---

## Documents to Update

### 1. PMOVES.AI Services and Integrations.md

**File:** `/home/pmoves/PMOVES.AI/docs/PMOVES.AI Services and Integrations.md`

**Current State:** 100,855 bytes, last updated 2025-01-05

**Updates Required:**
- [ ] Add new submodules from audit:
  - PMOVES-A2UI (fork of google/A2UI)
  - PMOVES-E2B-Danger-Room
  - PMOVES-AgentGym
  - PMOVES-surf
- [ ] Document 5-tier network segmentation
- [ ] Document 6-tier environment architecture
- [ ] Add Docker hardening section (USER directives)
- [ ] Update service count (currently 45, now 48+)
- [ ] Add namespace publishing patterns (GHCR lowercase)
- [ ] Document Tailscale integration for remote access

**New Sections to Add:**
```markdown
## 6-Tier Environment Architecture

### Principle of Least Privilege via Secret Segmentation

PMOVES implements 6 specialized environment tiers for secrets management...

## Docker Hardening Best Practices

### USER Directives (P0 Security)

All services MUST run as non-root users:

```dockerfile
RUN groupadd -r pmoves -g 1000 && \
    useradd -r -u 1000 -g pmoves -s /sbin/nologin pmoves
USER pmoves
```

### Namespace Publishing (GHCR)

GHCR requires lowercase namespaces. Normalize in CI/CD:
```
POWERFULMOVES -> powerfulmoves
```

## Tailscale VPN Configuration

Production access via Tailscale:
```
tailscale up --advertise-exit-node
```
```

### 2. PMOVES_Git_Organization.md

**File:** `/home/pmoves/PMOVES.AI/docs/PMOVES_Git_Organization.md`

**Current State:** Last updated 2025-01-05, contains Phase 1-2 security info

**Updates Required:**
- [ ] Update Phase 3 status (Q1 2026 target)
- [ ] Add latest GitHub Actions patterns (JIT runners, ARC)
- [ ] Update branch protection rules to latest GitHub API
- [ ] Add CODEOWNERS enforcement documentation
- [ ] Document Dependabot configuration updates
- [ ] Add submodule upstream sync procedures

**References to Update:**
- GitHub Rulesets API (latest)
- GitHub Actions self-hosted runners v2.329.0+
- Docker BuildKit cache patterns
- GHCR authentication with `DOCKER_CONFIG`

### 3. Security-Hardening-Roadmap.md

**File:** `/home/pmoves/PMOVES.AI/docs/Security-Hardening-Roadmap.md`

**Current State:** Generated 2025-12-06, Phase 1-2 complete

**Updates Required:**
- [ ] Update Phase 3 timeline (Q1 2026)
- [ ] Add Phase 3 initiatives from latest security research:
  - mTLS between service tiers
  - Falco runtime security monitoring
  - SLSA provenance attestation
  - Automated secret rotation
- [ ] Update security score baseline (95/100 → target 98/100)
- [ ] Document USER directive completion (29/29 services)
- [ ] Add 6-tier environment architecture
- [ ] Update compliance mappings (SOC 2, PCI DSS, NIST)

### 4. PMOVES.AI-Edition-Hardened-Full.md

**File:** `/home/pmoves/PMOVES.AI/docs/PMOVES.AI-Edition-Hardened-Full.md`

**Current State:** 70,093 bytes, comprehensive but dated

**Updates Required:**
- [ ] Update from 5-tier to clarify both network (5) and environment (6) tiers
- [ ] Add latest GitHub Actions patterns
- [ ] Update Docker hardening section with:
  - BuildKit secrets
  - Multi-stage builds
  - Distroless images
  - USER directive examples
- [ ] Add namespace publishing patterns
- [ ] Document Tailscale configuration for production
- [ ] Update service catalog count
- [ ] Add observability patterns (Loki, Prometheus, Grafana)
- [ ] Document CI/CD pipeline with Trivy scanning

---

## New Documentation to Create

### docs/production/Tailscale-Integration.md

Production VPN access configuration:
```bash
# Install Tailscale on all nodes
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate
tailscale up --authkey=${TS_AUTH_KEY}

# Advertise as exit node for remote access
tailscale up --advertise-exit-node

# Enable subnet router (if needed)
tailscale up --advertise-routes=172.30.0.0/16
```

### docs/production/GHCR-Namespace-Publishing.md

Docker image publishing with lowercase namespace:
```yaml
# Normalize org name to lowercase
- name: Build and push
  run: |
    ORG=$(echo '${{ github.repository_owner }}' | tr '[:upper:]' '[:lower:]')
    docker tag app:${GITHUB_SHA} ghcr.io/${ORG}/app:${GITHUB_SHA}
    docker push ghcr.io/${ORG}/app:${GITHUB_SHA}
```

### docs/architecture/6-tier-environment-architecture.md

Detailed documentation of the 6-tier environment secret architecture.

---

## External References to Refresh

### GitHub Official Documentation
- [ ] GitHub Actions Security Hardening (latest)
- [ ] GitHub Rulesets API v3
- [ ] GitHub Dependabot configuration
- [ ] GitHub Actions Runner Controller (ARC)
- [ ] GitHub Advanced Security features

### Docker Official Documentation
- [ ] Docker BuildKit latest patterns
- [ ] Docker multi-stage builds best practices
- [ ] Docker security scanning with Trivy
- [ ] Docker Compose network isolation
- [ ] Docker USER directive recommendations

### Security Standards
- [ ] CIS Docker Benchmark 1.0.0
- [ ] NIST Container Security Guidelines
- [ ] OWASP Docker Top 10
- [ ] Kubernetes Pod Security Standards

---

## Update Workflow

1. **Fetch Latest Documentation**
   ```bash
   # GitHub CLI latest docs
   gh api repos/POWERFULMOVES/PMOVES.AI/rulesets

   # Docker best practices
   curl -s https://docs.docker.com/engine/security/ | grep -A5 "USER"
   ```

2. **Update Each Document**
   - Read existing content
   - Identify sections requiring updates
   - Add new sections for missing content
   - Update external references
   - Verify cross-references between documents

3. **Validation Checklist**
   - [ ] All 5 network tiers documented
   - [ ] All 6 environment tiers documented
   - [ ] New submodules included
   - [ ] Namespace publishing patterns clear
   - [ ] Tailscale configuration documented
   - [ ] External references current (within 3 months)
   - [ ] Cross-references consistent

4. **Review and Commit**
   ```bash
   # Stage documentation updates
   git add docs/

   # Create PR for review
   git checkout -b docs/comprehensive-update-2026-01-29
   git commit -m "docs: Comprehensive documentation refresh

   - Update network tier documentation (5 tiers)
   - Add environment tier architecture (6 tiers)
   - Include new submodules from audit
   - Refresh GitHub/Docker official references
   - Document namespace publishing patterns
   - Add Tailscale production configuration

   Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

   gh pr create --title "docs: Comprehensive documentation refresh"
   ```

---

## Priority Matrix

| Document | Priority | Dependencies | Estimated Effort |
|----------|----------|--------------|------------------|
| PMOVES.AI-Edition-Hardened-Full.md | P0 | All others | 4 hours |
| network-tier-segmentation.md | P0 | None | 2 hours |
| PMOVES_Git_Organization.md | P1 | Hardened-Full | 3 hours |
| Security-Hardening-Roadmap.md | P1 | Hardened-Full | 2 hours |
| PMOVES.AI Services and Integrations.md | P2 | Hardened-Full | 3 hours |

**Total Estimated Effort:** 14 hours

---

## Tracking

- [ ] Phase 1: Update architecture documentation (network + environment tiers)
- [ ] Phase 2: Refresh external references (GitHub, Docker, security standards)
- [ ] Phase 3: Add new sections (Tailscale, namespace publishing, submodules)
- [ ] Phase 4: Validation and review
- [ ] Phase 5: PR and merge

---

**Next Steps:**
1. Begin with `PMOVES.AI-Edition-Hardened-Full.md` (foundational doc)
2. Update `network-tier-segmentation.md` to add environment tier context
3. Refresh external references in all documents
4. Create new documentation files
5. Validation and PR
