# Submodule Integration Checklist

**Purpose:** Checklist for integrating new services into PMOVES.AI.

**Last Updated:** 2026-02-12

---

## Phase 1: Preparation

- [ ] **Fork upstream repository** to POWERFULMOVES organization
- [ ] **Verify fork exists** at `github.com/POWERFULMOVES/PMOVES-ServiceName`
- [ ] **Clone fork locally** for testing
- [ ] **Create hardened branch** (`PMOVES.AI-Edition-Hardened`) from main
- [ ] **Push hardened branch** to origin

---

## Phase 2: Integration Files

### CHIT Manifest

- [ ] **Copy CHIT v2 template** to `chit/secrets_manifest_v2.yaml`
- [ ] **Define service slug** (lowercase with hyphens)
- [ ] **Set service tier** (api, agent, llm, worker, media, data)
- [ ] **List all ports** exposed by service
- [ ] **Define required secrets** with descriptions
- [ ] **Define optional secrets** with defaults
- [ ] **Add environment variable groups** (development, production)
- [ ] **Specify container definitions** (image, ports, environment)

### Integration Documentation

- [ ] **Copy integration template** to `PMOVES.AI_INTEGRATION.md`
- [ ] **Fill in service overview** (name, slug, description)
- [ ] **Document all ports** with purposes
- [ ] **List all environment variables** (infrastructure + service-specific)
- [ ] **Document NATS subjects** (published and subscribed)
- [ ] **List services used** (dependencies)
- [ ] **Add health monitoring section**
- [ ] **Document deployment differences** (standalone vs docked)
- [ ] **Include development instructions**
- [ ] **Add troubleshooting section**

### Integration Packages

- [ ] **Copy pmoves_announcer/** package** (or implement service announcements)
- [ ] **Copy pmoves_registry/** package** (or implement service discovery)
- [ ] **Copy pmoves_health/** package** (or implement /healthz endpoint)
- [ ] **Copy pmoves_common/** package** (for type consistency)

---

## Phase 3: Parent Repository Updates

### .gitmodules

- [ ] **Add submodule entry** to `.gitmodules` in appropriate category
- [ ] **Use consistent path** (`PMOVES-ServiceName`)
- [ ] **Use POWERFULMOVES** organization URL
- [ ] **Set branch to** `PMOVES.AI-Edition-Hardened`
- [ ] **Use literal tab** before `branch` (not spaces)

### Documentation

- [ ] **Add entry to** `pmoves/docs/SUBMODULE_LIST.md`
- [ ] **Include in appropriate category** (Agent, Knowledge, Voice, etc.)
- [ ] **Document health endpoint URL**
- [ ] **Document service tier**

### Docker Compose

- [ ] **Add service definition** to `pmoves/docker-compose.pmoves.yml`
- [ ] **Use service anchors** if applicable
- [ ] **Add to appropriate network** (`pmoves_app`, `pmoves_api`, etc.)
- [ ] **Map ports correctly**
- [ ] **Link environment variables** to secrets
- [ ] **Set restart policy** (`unless-stopped`)

### Environment Variables

- [ ] **Add service credentials** to `pmoves/env.shared` (if common)
- [ ] **Or add to tier-specific file** (`env.tier-llm`, `env.tier-api`, etc.)
- [ ] **Use `{{SERVICE_NAME}}_API_KEY`** pattern
- [ ] **Document all new variables** in integration doc

### CHIT Manifest

- [ ] **Register service secrets** in `pmoves/chit/secrets_manifest_v2.yaml`
- [ ] **Add service to groups** (tier assignment)
- [ ] **Specify secret sources** (env, chit_vault, docker_secret)

---

## Phase 4: Testing

### Service Health

- [ ] **Start service locally:** `docker compose up service-name`
- [ ] **Verify /healthz endpoint** returns 200 OK
- [ ] **Check health response** includes all dependency checks
- [ ] **Test with required secrets** (simulate production)
- [ ] **Test with optional secrets** missing (verify degraded state)

### Service Discovery

- [ ] **Verify service announces** on startup to NATS
- [ ] **Check services.announce.v1** subject for announcements
- [ ] **Verify pmoves_registry** can discover service
- [ ] **Test service URL resolution** from other services

### Integration

- [ ] **Test in standalone mode** (local dependencies)
- [ ] **Test in docked mode** (PMOVES.AI integration)
- [ ] **Verify NATS connection** in both modes
- [ ] **Check service discovery** in both modes
- [ ] **Test credential loading** from tier files

---

## Phase 5: Documentation Review

### Integration Documentation

- [ ] **Verify all sections** filled in `PMOVES.AI_INTEGRATION.md`
- [ ] **Check links to related docs** work
- [ ] **Verify examples are accurate**
- [ ] **Check troubleshooting section** covers common issues

### Service README

- [ ] **Update main README.md** with PMOVES.AI integration notes
- [ ] **Add PMOVES badge** if applicable
- [ ] **Document environment variables**
- [ ] **Include quick start guide**

---

## Phase 6: PR and Merge

### Create Pull Request

- [ ] **Create PR** from main → `PMOVES.AI-Edition-Hardened`
- [ ] **Use descriptive title:** "chore(integration): Add PMOVES.AI integration"
- [ ] **Include checklist** in PR description
- [ ] **Link to parent PR** (if updating parent)

### Parent Repository

- [ ] **Create PR** to parent PMOVES.AI repository
- [ ] **Title:** "chore(submodules): Add PMOVES-ServiceName"
- [ ] **Include integration checklist** in description
- [ ] **Reference hardened branch commit**

### Post-Merge

- [ ] **Update submodule tracking** in `SUBMODULE_COMMIT_REVIEW_*.md`
- [ ] **Add to CI/CD pipeline** if needed
- [ ] **Update service registry** documentation
- [ ] **Announce in team channel**

---

## Phase 7: Validation

### Smoke Tests

- [ ] **Run service smoke tests**
- [ ] **Verify health monitoring**
- [ ] **Check service discovery**
- [ ] **Test with production credentials**

### Integration Tests

- [ ] **Test with dependent services**
- [ ] **Test NATS messaging**
- [ ] **Test credential loading**
- [ ] **Verify deployment**

---

## Quick Reference

### Add New Submodule Commands

```bash
# 1. Fork and clone
gh repo fork upstream/repo --org POWERFULMOVES
git clone git@github.com:POWERFULMOVES/PMOVES-Service.git
cd PMOVES-Service
git checkout -b PMOVES.AI-Edition-Hardened
git push -u origin PMOVES.AI-Edition-Hardened

# 2. Add to parent
cd ../PMOVES.AI
git submodule add -b PMOVES.AI-Edition-Hardened \
  https://github.com/POWERFULMOVES/PMOVES-Service.git \
  PMOVES-Service
git commit -m "chore(submodules): Add PMOVES-Service"
git push

# 3. Copy integration files
cd PMOVES-Service
cp ../pmoves/templates/submodule/chit/secrets_manifest_v2.yaml \
   chit/secrets_manifest_v2.yaml
cp ../pmoves/templates/submodule/PMOVES.AI_INTEGRATION.md \
   PMOVES.AI_INTEGRATION.md

# 4. Update parent docs
cd ../PMOVES.AI
vim pmoves/docs/SUBMODULE_LIST.md
vim pmoves/docker-compose.pmoves.yml
vim pmoves/env.shared
git add .
git commit -m "feat(integration): Add PMOVES-Service"
git push
```

---

## Related Documentation

- [PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md](PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md) - Full integration guide
- [SUBMODULE_WORKFLOW.md](SUBMODULE_WORKFLOW.md) - Workflow documentation
- [CHIT_V2_SPECIFICATION.md](CHIT_V2_SPECIFICATION.md) - CHIT manifest format
- [NATS_SERVICE_DISCOVERY.md](NATS_SERVICE_DISCOVERY.md) - Service discovery patterns

---

**Maintainer:** PMOVES.AI Team
