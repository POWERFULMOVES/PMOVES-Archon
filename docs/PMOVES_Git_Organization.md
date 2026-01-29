# PMOVES Git Organization & Infrastructure Guide

This document provides a comprehensive guide to PMOVES.AI's GitHub organization, infrastructure setup, and related resources.

## Table of Contents
- [Contributor Guidance](#contributor-guidance)
- [Security Roadmap](#security-roadmap)
- [Branch Protection Rules](#branch-protection-rules)
- [Recent Changes](#recent-changes)
- [GitHub Actions Self-Hosted Runner Setup](#github-actions-self-hosted-runner-setup)
- [GitHub Documentation Resources](#github-documentation-resources)
- [PMOVES Project Repositories](#pmoves-project-repositories)
- [Infrastructure & Deployment](#infrastructure--deployment)
- [Video Resources & Tutorials](#video-resources--tutorials)
- [Team & Collaboration](#team--collaboration)

---

## Contributor Guidance
- Operational/stabilization rules live in the root `AGENTS.md`; service-level coding norms for the `pmoves/` subtree live in `pmoves/AGENTS.md`. Read both before opening PRs and keep edits in sync.
- Submodules are the source of truth for hardened integrations (Archon, Agent Zero, PMOVES.YT, etc.). Pin the intended branch/ref in `.gitmodules`, align with `docs/PMOVES.AI-Edition-Hardened-Full.md`, and note any temporary divergence in PR notes.

---

## Security Roadmap

### Phase 1: Foundation - COMPLETE ✅
**Completion Date:** 2025-11-15
**Security Score:** 80/100

**Achievements:**
- GitHub Actions hardening with secure workflow patterns
- Non-root baseline established (3/29 services migrated)
- SecurityContext templates for pod security standards
- Initial container security posture

### Phase 2: Hardening - COMPLETE ✅
**Completion Date:** 2025-12-07 (PR #276, commit 8bf936a)
**Security Score:** 95/100 (+18.75% improvement)

**Achievements:**
- **BuildKit Secrets Migration:** Removed 4 HIGH-RISK secrets from Archon Dockerfile, migrated to BuildKit `--secret` pattern
- **Network Tier Segmentation:** 5-tier isolation architecture across 45 services
  - Tier 1: Public (Jellyfin, TensorZero UI)
  - Tier 2: Gateway (TensorZero, Agent Zero)
  - Tier 3: Application (Hi-RAG, Archon, PMOVES.YT)
  - Tier 4: Data (Supabase, Qdrant, Neo4j, Meilisearch)
  - Tier 5: Infrastructure (NATS, MinIO, Prometheus)
- **Branch Protection:** Main branch protected with required PR reviews, status checks, signed commits, and linear history
- **CODEOWNERS:** Automated review assignments for critical paths

**Documentation:** 67KB of Phase 2 security guides and audit logs

### Phase 3: Advanced Security - Q1 2026
**Target Completion:** Q1 2026 (Weeks 1-12)
**Target Security Score:** 98/100 (from current 95/100)

**Planned Initiatives (by week):**

**Week 1-2: Complete Phase 2 Gaps**
- BuildKit secrets migration (Archon Dockerfile - lines 49-79)
- Branch protection rules (user implementation via GitHub UI)
- Kubernetes NetworkPolicy manifests

**Week 3-4: Secret Rotation Mechanism**
- Deploy External Secrets Operator
- Configure HashiCorp Vault backend
- Create SecretStore manifests
- Create rotation CronJobs (90-day max age)
- Test secret rotation with dual-key overlap

**Week 5-6: TLS/mTLS for P0 Services**
- Deploy cert-manager for Kubernetes
- Create internal CA (pmoves-internal-ca)
- Issue service certificates (90-day validity)
- Configure mTLS for TensorZero, NATS
- Auto-renew certificates 15 days before expiry

**Week 7-8: Security Scanning**
- Deploy Trivy in CI/CD
- Configure Gitleaks secret scanning
- kube-bench CIS benchmark
- SARIF upload to GitHub Security
- Automated remediation pipeline

**Week 9-10: SLSA + Pod Security**
- SLSA provenance generation
- cosign signature verification
- Kyverno admission controller
- Pod Security Standards enforcement
- seccomp profiles

**Week 11-12: Runtime Monitoring**
- Deploy Falco for runtime monitoring
- Configure alert rules
- Integration with Loki for log aggregation
- Create incident response playbooks

**Success Criteria:**
- Security score: 98%+ (from current 95%)
- Zero CRITICAL vulnerabilities in production
- <5 HIGH vulnerabilities in production
- All P0 services use mTLS
- SLSA provenance on all production images
- Pod Security Standards enforced
- All secrets rotated automatically

---

## Branch Protection Rules

### Default branch merge rules (Rulesets)
PMOVES.AI uses **GitHub Rulesets** on the default branch (not classic branch protection). This matters because the REST endpoint for branch protection can return 404 even when merges are still gated.

**Inspect the active ruleset (recommended):**
- List rulesets: `gh api repos/POWERFULMOVES/PMOVES.AI/rulesets`
- View a ruleset: `gh api repos/POWERFULMOVES/PMOVES.AI/rulesets/<id>`
- Quick summary (human-readable): `gh api repos/POWERFULMOVES/PMOVES.AI/rulesets/<id> | jq '{enforcement,conditions,rules: [.rules[].type]}'`

**Current expected gates (as of 2025-12-15):**
- Pull requests required
- Code owner review required (see `.github/CODEOWNERS`)
- Last-push approval required (someone other than the last pusher must approve)
- Review threads must be resolved before merge
- Prevent deletion + non-fast-forward updates on the default branch
- Allowed merge methods: merge, squash, rebase

### CODEOWNERS
Automated review assignments are configured in `.github/CODEOWNERS` and are authoritative (inspect it directly: `.github/CODEOWNERS`). This repo intentionally keeps owners narrow for security-critical paths (workflows, compose, env, and core services).

**Status:** Active and enforced since PR #276 (2025-12-07)

---

## Recent Fixes

### Docker Auth + Build Stability (2025-12-13)
**Status:** Complete ✅

- **Docker credential helper mismatch:** Docker Desktop/WSL commonly writes `credsStore=desktop.exe` into `~/.docker/config.json`. On Linux/headless hosts this can break pulls/builds with `docker-credential-desktop.exe: permission denied`.
  - **Preferred fix:** use the repo-scoped Docker config under `.docker-nocreds/` and set `DOCKER_CONFIG` accordingly.
  - The `pmoves/Makefile` now auto-prefers `../.docker-nocreds` when present so `make -C pmoves up-*` and `make -C pmoves update` work in headless environments.
  - **GHCR login tip (local):** use the same repo-scoped config when logging into GHCR, otherwise Docker will try to save credentials via the broken helper:
    - `DOCKER_CONFIG=./.docker-nocreds gh auth token | DOCKER_CONFIG=./.docker-nocreds docker login ghcr.io -u <USER> --password-stdin`
    - Note: run this from the repository root (or adjust the relative `.docker-nocreds` path accordingly).
    - Safety note: avoid `docker login` without `DOCKER_CONFIG` on headless hosts unless you intentionally want credentials written to `~/.docker/config.json`.
- **Compose file subsets:** invoking `docker compose` with different `-f` subsets under the same project name can cause noisy “Found orphan containers” warnings (and confusing status output). Prefer the `pmoves/Makefile` targets, which operate on a consistent compose file set for the `pmoves` stack.
- **Buildx drift:** stale Docker Desktop/WSL buildx builders can reference dead `/run/desktop/mnt/host/wsl/...` bind mounts. Switch to the default builder (`docker buildx use default`) or recreate the builder if builds fail.
- **GHCR publish scope:** pushing images to GHCR requires a token with `write:packages` (and `read:packages` for pulls of private packages). For GitHub CLI tokens: `gh auth refresh -h github.com -s write:packages`.
  - If `gh auth refresh` rate-limits with `slow_down`, wait ~30–60 seconds and retry (GitHub device flow throttles repeated attempts).
- **GHCR namespace casing:** GHCR image references must use a lowercase namespace. If your org/user owner is uppercase (e.g., `POWERFULMOVES`), normalize tags to lowercase in CI/CD (the integrations GHCR workflow now does this).
- **dotenv safety + compose overrides:** avoid `source`-ing `pmoves/env.shared` directly in shell scripts/Make recipes (it may contain non-shell-safe values). Prefer `pmoves/scripts/with-env.sh`, which sanitizes dotenv files before exporting vars.
- **Secrets precedence:** avoid Compose-time `environment: VAR=${VAR}` for secrets that are already in `env_file`, because an unset shell var becomes an empty string and overrides the `env_file` value inside containers. This surfaced as Open Notebook tokens drifting from DeepResearch until the compose interpolation was removed.
- **n8n flow versioning:** canonical, shareable exports live under `pmoves/n8n/flows/` and are mirrored into the `PMOVES-n8n` submodule (`PMOVES-n8n/workflows/`). Import/activate with `make -C pmoves n8n-bootstrap` (handles import + DB sanitize + restart). Refresh exports from a live n8n instance via `make -C pmoves n8n-export-repo-flows`.
- **n8n HTTP timeouts:** `options.timeout` for HTTP Request nodes is **milliseconds** in n8n. Treat values like `10/20/30` as 10ms/20ms/30ms unless explicitly multiplied (this has bitten Voice Agent flows and Supabase/NATS calls).
- **Voice Agents (Flute):** Voice Agent router (`pmoves/n8n/flows/voice_platform_router.json`) defaults to TensorZero local models when available (`VOICE_AGENT_MODEL=tensorzero::model_name::qwen2_5_14b`) and publishes `voice.agent.response.v1` to NATS.

### Docker Build Reliability Improvements (2025-12-06 to 2025-12-07)
**Status:** Complete ✅

Following Phase 2 Security Hardening, we identified and resolved critical Docker build failures across the stack:

**Critical Issues Fixed:**
1. **DeepResearch** — container restart loop and build wiring
   - Commit `4a2a36a6` restored the runtime `contracts/` copy in `pmoves/services/deepresearch/Dockerfile` and updated `pmoves/docker-compose.yml` so the container stopped crash-looping.
2. **Dockerfiles (root context)** — COPY-path fixes for services building from the repo root
   - Commit `d6c5381e` corrected COPY paths in `pmoves/services/chat-relay/Dockerfile` and `pmoves/services/flute-gateway/Dockerfile`.
3. **FFmpeg-Whisper** — scoped build context and safer ignore rules
   - Commit `714681db` updated `pmoves/services/ffmpeg-whisper/Dockerfile`, `pmoves/docker-compose.yml`, and the repo root `.dockerignore`.

**Build Success Rate**: Improved from intermittent failures to 100% successful builds for affected services

**See Also**: `docs/build-fixes-2025-12-07.md` for the detailed timeline and root-cause analysis.

---

## Recent Changes

### PR #276: Phase 2 Security Hardening (2025-12-07)
**Status:** Merged to main (commit 8bf936a)

**Changes:**
- Fixed network isolation tier assignments for all 45 services
- Container security fixes:
  - TensorZero: Non-root user, read-only root filesystem
  - DeepResearch: Fixed build context and environment variable syntax
  - NATS: Proper health check configuration
- Removed BuildKit secrets from tracked files
- Implemented branch protection rules
- Added CODEOWNERS for automated reviews

**Key Commits:**
- a15c045: Network tier segmentation fixes
- 0811f96: TensorZero container hardening
- cb47f06: DeepResearch build fixes
- 4a2a36a: Branch protection setup

**Documentation:** See `docs/security/phase-2/` for complete audit trail

### Production Readiness Enhancements (2025-12-07, commit 7bacba2)
**Status:** Complete ✅

**TensorZero Model Expansion:**
- Added 5 new Qwen models for local inference via Ollama:
  - Qwen2.5 32B (flagship, ~19GB)
  - Qwen2.5 14B (efficient, ~8GB)
  - Qwen2-VL 7B (vision-language, ~5GB)
  - Qwen3-Reranker 4B (cross-encoder for Hi-RAG v2)
- Enabled ClickHouse observability in TensorZero config

**GitHub Automation:**
- Created .github/CODEOWNERS for security-critical path approvals
- Configured Dependabot for Docker, GitHub Actions, and Python dependencies
- Weekly automated dependency update schedule

**Documentation Updates (via TAC parallel agents):**
- Updated PMOVES.AI-Edition-Hardened-Full.md (service count, network architecture, security posture)
- Created docs/architecture/network-tier-segmentation.md (421 lines, 5-tier architecture)
- Updated .gitignore patterns for backup files and WSL2 artifacts

---

## GitHub Actions Self-Hosted Runner Setup

### Prerequisites
- Linux x64 environment
- Appropriate permissions to install and configure runners

### Installation Steps

1. **Create a folder for the runner**
   ```bash
   mkdir actions-runner && cd actions-runner
   ```

2. **Download the latest runner package**
   ```bash
   curl -o actions-runner-linux-x64-2.329.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.329.0/actions-runner-linux-x64-2.329.0.tar.gz
   ```

3. **Optional: Validate the hash**
   ```bash
   echo "194f1e1e4bd02f80b7e9633fc546084d8d4e19f3928a324d512ea53430102e1d  actions-runner-linux-x64-2.329.0.tar.gz" | shasum -a 256 -c
   ```

4. **Extract the installer**
   ```bash
   tar xzf ./actions-runner-linux-x64-2.329.0.tar.gz
   ```

### Configuration

1. **Create the runner and start the configuration experience**
   ```bash
   ./config.sh --url https://github.com/POWERFULMOVES/PMOVES.AI --token <RUNNER_REGISTRATION_TOKEN>
   ```
   Obtain a one-time registration token for your runner from the GitHub UI (Settings → Actions → Runners). Never commit real tokens to the repository or documentation.

2. **Run the runner**
   ```bash
   ./run.sh
   ```

### Using Your Self-Hosted Runner

Add this YAML to your workflow file for each job:

```yaml
runs-on: self-hosted
```

---

## GitHub Documentation Resources

### Actions & Runners
- [Self-hosted runners overview](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners)
- [Self-hosted runners concepts](https://docs.github.com/en/actions/concepts/runners/self-hosted-runners)
- [Private networking for runners](https://docs.github.com/en/actions/concepts/runners/private-networking)
- [Runner groups](https://docs.github.com/en/actions/concepts/runners/runner-groups)
- [Actions Runner Controller](https://docs.github.com/en/actions/concepts/runners/actions-runner-controller)

### Workflows & Automation
- [Using workflow templates](https://docs.github.com/en/actions/how-tos/write-workflows/use-workflow-templates)
- [Monitoring workflows](https://docs.github.com/en/actions/how-tos/monitor-workflows)

### Repository Management
- [About GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)
- [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [Deciding when to build a GitHub App](https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/deciding-when-to-build-a-github-app)

### Security & Dependencies
- [Dependabot configuration template](https://github.com/POWERFULMOVES/PMOVES.AI/new/main?dependabot_template=1&filename=.github%2Fdependabot.yml)

### Secrets & Package Publishing (Org Standard)
- Store credentials only in GitHub Secrets (org/repo/env scope) and the team vault; never in tracked files.
- Standard secret names: `GH_PAT_PUBLISH`, `GHCR_USERNAME`, `DOCKERHUB_PAT`, `DOCKERHUB_USERNAME`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `YOUTUBE_API_KEY`, `GOOGLE_OAUTH_CLIENT_SECRET`, `DISCORD_WEBHOOK` (add more as needed; keep them documented in `docs/SECRETS_ONBOARDING.md`).
- Image publishing: workflows should `docker/login-action` to GHCR and Docker Hub using the secrets above, then `docker/build-push-action` with SBOM+provenance and signed tags.

---

## PMOVES Project Repositories

### Core Components
| Repository | Description | Upstream |
|------------|-------------|----------|
| [PMOVES-Creator](https://github.com/POWERFULMOVES/PMOVES-Creator.git) | Content creation and management tools | - |
| [PMOVES-Agent-Zero](https://github.com/POWERFULMOVES/PMOVES-Agent-Zero.git) | Primary agent system | - |
| [PMOVES-Archon](https://github.com/POWERFULMOVES/PMOVES-Archon.git) | Architecture and orchestration layer | - |
| [PMOVES-Deep-Serch](https://github.com/POWERFULMOVES/PMOVES-Deep-Serch.git) | Advanced search capabilities | - |
| [PMOVES-HiRAG](https://github.com/POWERFULMOVES/PMOVES-HiRAG.git) | Hierarchical Retrieval-Augmented Generation | - |

### AI & Research (New)
| Repository | Description | Upstream |
|------------|-------------|----------|
| [PMOVES-A2UI](https://github.com/POWERFULMOVES/PMOVES-A2UI.git) | Agent-to-User Interface (fork of google/A2UI) | [google/A2UI](https://github.com/google/A2UI.git) |
| [PMOVES-AgentGym](https://github.com/POWERFULMOVES/PMOVES-AgentGym.git) | Agent training and evaluation environment | [WooooDyy/AgentGym](https://github.com/WooooDyy/AgentGym) |
| [PMOVES-E2B-Danger-Room](https://github.com/POWERFULMOVES/PMOVES-E2B-Danger-Room.git) | Code execution sandbox environment | [e2b-dev/e2b](https://github.com/e2b-dev/e2b) |
| [PMOVES-surf](https://github.com/POWERFULMOVES/pmoves-surf.git) | Web navigation and browsing | - |
| [PMOVES-Pipecat](https://github.com/POWERFULMOVES/pmoves-pipecat.git) | Multimodal voice communication | [pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat) |
| [PMOVES-tensorzero](https://github.com/POWERFULMOVES/PMOVES-tensorzero.git) | LLM gateway and observability | [tensorzero/tensorzero](https://github.com/tensorzero/tensorzero) |

### Media & Content
| Repository | Description | Upstream |
|------------|-------------|----------|
| [PMOVES.YT](https://github.com/POWERFULMOVES/PMOVES.YT.git) | YouTube integration and processing | - |
| [PMOVES-Jellyfin](https://github.com/POWERFULMOVES/PMOVES-Jellyfin.git) | Media server integration | - |
| [Pmoves-Jellyfin-AI-Media-Stack](https://github.com/POWERFULMOVES/Pmoves-Jellyfin-AI-Media-Stack.git) | AI-powered media processing stack | - |

### Tools & Utilities
| Repository | Description | Upstream |
|------------|-------------|----------|
| [PMOVES-Open-Notebook](https://github.com/POWERFULMOVES/PMOVES-Open-Notebook.git) | Notebook and documentation system | [lfnovo/open-notebook](https://github.com/lfnovo/open-notebook) |
| [Pmoves-Health-wger](https://github.com/POWERFULMOVES/Pmoves-Health-wger.git) | Health and fitness integration | [wger-project/wger](https://github.com/wger-project/wger) |
| [PMOVES-Wealth](https://github.com/POWERFULMOVES/PMOVES-Wealth.git) | Financial management tools | [firefly-iii/firefly-iii](https://github.com/firefly-iii/firefly-iii) |
| [PMOVES-BoTZ](https://github.com/POWERFULMOVES/PMOVES-BoTZ.git) | Bot and automation toolkit | - |
| [PMOVES-ToKenism-Multi](https://github.com/POWERFULMOVES/PMOVES-ToKenism-Multi.git) | Multi-token management system | - |
| [PMOVES-DoX](https://github.com/POWERFULMOVES/PMOVES-DoX.git) | Documentation and knowledge management | - |
| [PMOVES-n8n](https://github.com/POWERFULMOVES/PMOVES-n8n.git) | Workflow automation platform | [n8n-io/n8n](https://github.com/n8n-io/n8n) |
| [PMOVES-MAI-UI](https://github.com/POWERFULMOVES/PMOVES-MAI-UI.git) | Multimodal Agent Interface | - |
| [PMOVES-transcribe-and-fetch](https://github.com/POWERFULMOVES/PMOVES-transcribe-and-fetch.git) | Media transcription utilities | - |
| [pmoves-e2b-mcp-server](https://github.com/POWERFULMOVES/pmoves-e2b-mcp-server.git) | E2B MCP integration | - |

### Infrastructure & Networking
| Repository | Description | Upstream |
|------------|-------------|----------|
| [PMOVES-Remote-View](https://github.com/POWERFULMOVES/PMOVES-Remote-View.git) | Remote access and viewing capabilities | - |
| [PMOVES-Tailscale](https://github.com/POWERFULMOVES/PMOVES-Tailscale.git) | VPN and network integration | - |
| [PMOVES-Danger-infra](https://github.com/POWERFULMOVES/PMOVES-Danger-infra.git) | Infrastructure provisioning | - |
| [PMOVES-BotZ-gateway](https://github.com/POWERFULMOVES/PMOVES-BotZ-gateway.git) | Bot gateway service | - |
| [PMOVES-E2B-Danger-Room-Desktop](https://github.com/POWERFULMOVES/PMOVES-E2B-Danger-Room-Desktop.git) | Desktop E2B environment | - |
| [PMOVES-crush](https://github.com/POWERFULMOVES/PMOVES-crush.git) | Resource management | - |
| [PMOVES-Ultimate-TTS-Studio](https://github.com/POWERFULMOVES/PMOVES-Ultimate-TTS-Studio.git) | Text-to-speech studio | - |
| [PMOVES-Pinokio-Ultimate-TTS-Studio](https://github.com/POWERFULMOVES/PMOVES-Pinokio-Ultimate-TTS-Studio.git) | Pinokio TTS integration | - |
| [Pmoves-hyperdimensions](https://github.com/POWERFULMOVES/Pmoves-hyperdimensions.git) | Hyperdimensional computing | - |
| [Pmoves-AgentGym-RL](https://github.com/POWERFULMOVES/Pmoves-AgentGym-RL.git) | Reinforcement learning for agents | - |

**Submodule Sync Status:** See [docs/submodules-upstream-audit.md](submodules-upstream-audit.md) for detailed sync status, CI/CD health, and upstream PR candidates for all forked submodules.

---

## Infrastructure & Deployment

### Cloudflare Integration
- [Workers AI Configuration Bindings](https://developers.cloudflare.com/workers-ai/configuration/bindings/)
- [Pages Deploy Hooks](https://developers.cloudflare.com/pages/configuration/deploy-hooks/)

### Reference Implementations
- [Cloudflare AI Hono Durable Objects Example](https://github.com/elizabethsiegle/nbafinals-cloudflare-ai-hono-durable-objects.git) - Can be used to setup users on Cloudflare and add to GitHub users

### RustDesk Server Setup
For self-hosted remote desktop solutions:

- [Installation Guide](https://rustdesk.com/docs/en/self-host/rustdesk-server-oss/install/)
- [Docker Deployment](https://rustdesk.com/docs/en/self-host/rustdesk-server-oss/docker/)
- [Client Configuration](https://rustdesk.com/docs/en/self-host/client-configuration/)
- [Client Deployment](https://rustdesk.com/docs/en/self-host/client-deployment/)

---

## Video Resources & Tutorials

### ARCHON & Claude Code Integration
For running Claude Code in spinnable VMs with ARCHON:

- [Video 1](https://www.youtube.com/watch?v=XaYpdKGKKtY)
- [Video 2](https://www.youtube.com/watch?v=kFpLzCVLA20)
- [Video 3](https://www.youtube.com/watch?v=OIKTsVjTVJE)
- [Video 4](https://www.youtube.com/watch?v=p0mrXfwAbCg)

### Richard Aragon's Playlists
- [Complete Playlist Collection](https://www.youtube.com/@richardaragon8471/playlists)

---

## Team & Collaboration

### PMOVES.AI-Edition-Hardened
Specialized hardened edition for enhanced security and stability.

### Collaborators

| Username | Role |
|----------|------|
| hunnibear | Collaborator |
| Pmovesjordan | Collaborator |
| Barathicite | Collaborator |
| wdrolle | Collaborator |

---

## Additional Resources

### Claude AI Integration
- [Using the Connectors Directory to Extend Claude's Capabilities](https://support.claude.com/en/articles/11724452-using-the-connectors-directory-to-extend-claude-s-capabilities)

---

## Notes

- This document serves as a central reference for PMOVES.AI's GitHub organization and infrastructure
- Regular updates should be made as new repositories are added or configurations change
- Team members should ensure they have appropriate access to the repositories mentioned above
