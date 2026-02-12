# Atomic Commit Workflow for PMOVES.AI

**Purpose:** Define guidelines for atomic commits and targeted PRs in PMOVES.AI development.

**Last Updated:** 2026-02-12

---

## Overview

Atomic commits are the foundation of maintainable, reviewable code. An atomic commit represents a **single logical unit of change** that is self-contained, passes tests, and can be reviewed independently.

```
One Logical Unit = One Atomic Commit
```

### Benefits

- **Easier Review:** Smaller PRs are faster to review thoroughly
- **Safer Reverts:** Single logical units can be reverted without breaking other features
- **Better Bisect:** Git bisect can quickly identify problematic commits
- **Clear History:** Commit history tells a coherent story
- **PMOVES.AI Aware:** Commits respect submodule boundaries and integration patterns

---

## What Makes a Commit Atomic

### Definition

An atomic commit satisfies **all** of these criteria:

1. **Single Logical Purpose** - Addresses one concern only
2. **Self-Contained** - Includes all necessary code changes
3. **Passes Tests** - All tests pass after commit
4. **Reviewable** - Can be understood in 5-10 minutes
5. **No Side Effects** - Doesn't accidentally change unrelated behavior

### Examples

**Good Atomic Commit:**
```
feat(agent-zero): Add MCP service discovery endpoint

- Adds POST /mcp/discover for external services
- Includes service registration logic
- Updates pmoves_registry integration
- Adds integration tests
```

**Non-Atomic Commit (Too Large):**
```
feat(agent-zero): Add MCP integration and update Archon

- Adds MCP endpoints to Agent Zero
- Updates Archon to use new endpoints
- Changes pmoves_registry format
- Updates 5 different services to use new format
```
^^^ This should be 3-4 separate commits

**Non-Atomic Commit (Too Small/Incomplete):**
```
feat(agent-zero): Add function signature

- Adds empty function stub only
```
^^^ This doesn't pass tests or provide value

---

## PMOVES.AI Commit Scopes

### Submodule Update Commits

When updating a submodule (e.g., PMOVES-Agent-Zero):

```bash
# In submodule
cd PMOVES-Agent-Zero
git commit -m "feat(mcp): Add service discovery endpoint"

# Then in parent
cd ..
git add PMOVES-Agent-Zero
git commit -m "chore(submodules): Update Agent-Zero to abc123"
```

**Pattern:** `chore(submodules): Update <Service-Name> to <commit-sha>`

### Integration Pattern Commits

When adding PMOVES.AI integration to a service:

```bash
# 1. Add pmoves_announcer package
git commit -m "feat(integration): Add NATS service announcement"

# 2. Add pmoves_health package
git commit -m "feat(integration): Add /healthz endpoint"

# 3. Add pmoves_registry integration
git commit -m "feat(integration): Add service registry client"

# 4. Update PMOVES.AI parent
cd ../PMOVES.AI
git add PMOVES-NewService
git commit -m "chore(submodules): Add PMOVES-NewService integration"
```

### Documentation Commits

Documentation changes should be atomic by topic:

```bash
# Per-document commits
git commit -m "docs(submodules): Add PMOVES-NewService to catalog"
git commit -m "docs(chit): Update CHIT v2 specification"
git commit -m "docs(workflow): Add atomic commit guidelines"

# NOT one giant commit
git commit -m "docs: update everything"
```

### Environment Variable Commits

When adding service credentials:

```bash
# 1. Add to template (no secrets)
git add pmoves/env.shared.template
git commit -m "chore(credentials): Add NEW_SERVICE_URL template"

# 2. Document in CHIT manifest
git add pmoves/chit/secrets_manifest_v2.yaml
git commit -m "chore(chit): Register new-service-slug"
```

---

## Conventional Commit Format for PMOVES.AI

### Extended Format

PMOVES.AI uses extended conventional commits with PMOVES-specific scopes:

```
type(scope[sub-scope]): subject

[optional body detailing what and why]

[optional footer with references]
```

### PMOVES.AI Types

| Type | Purpose | Examples |
|--------|---------|------------|
| `feat` | New feature | `feat(agent-zero): Add MCP discovery` |
| `fix` | Bug fix | `fix(hirag): Handle empty query results` |
| `chore` | Maintenance | `chore(submodules): Update Agent-Zero` |
| `docs` | Documentation | `docs(submodules): Add service catalog` |
| `style` | Formatting | `style(python): Run black formatter` |
| `refactor` | Code restructuring | `refactor(registry): Simplify service lookup` |
| `perf` | Performance | `perf(whisper): Optimize GPU memory` |
| `test` | Test changes | `test(hirag): Add reranking tests` |
| `ci` | CI/CD | `ci(docker): Fix multiarch build` |

### PMOVES.AI Scopes

| Scope | Description | Examples |
|--------|-------------|------------|
| `agent-zero` | Agent Zero orchestrator | `feat(agent-zero): Add tool execution` |
| `archon` | Archon agent service | `fix(archon): Resolve form loading` |
| `botz` | BoTZ gateway | `feat(botz): Add skill endpoint` |
| `submodules` | Submodule updates | `chore(submodules): Sync all submodules` |
| `hirag` | Hi-RAG services | `feat(hirag): Add cross-encoder` |
| `tensorzero` | LLM gateway | `fix(tensorzero): Retry on timeout` |
| `integration` | PMOVES.AI integration | `feat(integration): Add NATS announcer` |
| `chit` | CHIT secret management | `docs(chit): Update spec v2` |
| `credentials` | Environment/secret config | `chore(credentials): Add new service keys` |
| `docker` | Docker/compose | `fix(docker): Fix networking` |
| `monitoring` | Prometheus/Grafana | `feat(monitoring): Add alert` |

### Sub-Scopes

For more specific targeting within a submodule:

```
feat(hirag[v2]): Add cross-encoder reranking
fix(agent-zero[mcp]): Resolve JSON parsing error
docs(submodules[catalog]): Add new service entry
```

---

## PR Size Guidelines

### Recommended Limits

| PR Type | Files | Lines Changed | Description |
|-----------|--------|---------------|-------------|
| **Bug Fix** | ≤ 5 | ≤ 100 | Quick fixes, single issue |
| **Feature** | ≤ 15 | ≤ 400 | Focused feature addition |
| **Refactor** | ≤ 20 | ≤ 500 | Internal reorganization |
| **Documentation** | ≤ 10 | N/A | Doc updates |
| **Submodule Sync** | ≤ 3 | ≤ 50 | Bumping submodule refs |

### When to Split PRs

**Split your PR if:**
- It modifies more than 3 submodules/services
- It exceeds recommended line counts
- Reviewer requests changes to unrelated parts
- It mixes feature work with refactoring
- It includes documentation that deserves its own review

**Split Strategy:**
```
1. Core Feature PR (main implementation)
   ↓
2. Follow-up Fix PR (addressed review feedback)
   ↓
3. Documentation PR (after feature is merged)
   ↓
4. Integration PR (connecting to other services)
```

---

## Atomic Commit Workflow

### Step-by-Step Process

1. **Start Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes and Stage Incrementally**
   ```bash
   # Make first logical unit
   # Edit files...
   git add file1.py file2.py
   git commit -m "feat(service): Add first unit"

   # Make second logical unit
   # Edit more files...
   git add file3.py
   git commit -m "feat(service): Add second unit"
   ```

3. **Before Pushing: Squash WIP Commits**
   ```bash
   # If you have "WIP", "fix typo", etc. commits:
   git rebase -i HEAD~5  # Interactive rebase
   # Combine related WIP commits into one atomic unit
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   gh pr create --title "feat(service): Add feature description"
   ```

### Handling Cross-File Changes

When a feature touches multiple files that **must** be committed together:

```bash
# Option 1: Stage all related files together
git add service.py client.py tests/test_service.py
git commit -m "feat(service): Add new endpoint with client support"

# Option 2: If truly separate units, split into two commits
git add service.py tests/test_service.py
git commit -m "feat(service): Add new endpoint"

git add client.py
git commit -m "feat(client): Add service integration"
```

---

## Git Bisect Friendliness

Atomic commits make `git bisect` effective:

```bash
# A bug was introduced between v1.0.0 and v1.1.0
git bisect start
git bisect bad v1.1.0
git bisect good v1.0.0

# Bisect will checkout each commit
# If atomic, each commit has clear purpose
# You can quickly identify which "feat" or "fix" caused the issue
```

### Non-Bisect-Friendly Patterns to Avoid

```
BAD: "Fix multiple things" commit
- Fixes service A timeout
- Updates service B auth
- Reformats service C
- Adds test for service D

^^^ Bisect can't identify which "fix" introduced the bug
```

---

## PMOVES.AI-Specific Patterns

### Service Integration Atomicity

When integrating a new service:

**Commit 1:** Add submodule reference
```bash
git add .gitmodules
git commit -m "chore(submodules): Add PMOVES-NewService"
```

**Commit 2:** Add to catalog
```bash
git add pmoves/docs/SUBMODULE_LIST.md
git commit -m "docs(submodules): Add PMOVES-NewService to catalog"
```

**Commit 3:** Add Docker configuration
```bash
git add pmoves/docker-compose.pmoves.yml
git commit -m "feat(docker): Add new-service container"
```

**Commit 4:** Add environment template
```bash
git add pmoves/env.shared.template
git commit -m "chore(credentials): Add NEW_SERVICE template"
```

### Multi-Submodule Updates

When updating multiple submodules (e.g., after branching strategy):

```bash
# Update first submodule
cd PMOVES-Agent-Zero
git pull
cd ..
git add PMOVES-Agent-Zero
git commit -m "chore(submodules): Update Agent-Zero to abc123"

# Update second submodule
cd PMOVES-Archon
git pull
cd ..
git add PMOVES-Archon
git commit -m "chore(submodules): Update Archon to def456"

# Do NOT combine into one commit
# git commit -m "chore(submodules): Update Agent-Zero and Archon"
```

### CHIT Manifest Updates

When updating CHIT v2 manifests:

```bash
# Separate commits for different aspects

# 1. Register new service
git commit -m "chore(chit): Register service-slug in manifest"

# 2. Update specification
git commit -m "docs(chit): Update CHIT v2 spec for new field"

# 3. Update documentation
git commit -m "docs(chit): Document new manifest format"
```

---

## Pre-Commit Hooks

### Recommended Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Check commit message format
npm run --if-present commitlint --edit $1

# Run quick tests
npm run --if-present test:fast

# Check for TODO comments
git diff --cached | grep "^+.*TODO" && echo "Remove TODOs first" && exit 1

# Check file size (warn if > 20 files)
FILES=$(git diff --cached --name-only | wc -l)
if [ $FILES -gt 20 ]; then
    echo "Warning: Committing $FILES files (consider splitting)"
fi
```

---

## Reviewing Atomic Commits

### During Code Review

**Checklist for Reviewers:**

- [ ] Commit message follows conventional format
- [ ] Single logical purpose
- [ ] All related changes included (no missing pieces)
- [ ] Tests included and passing
- [ ] No unrelated changes bundled
- [ ] PMOVES.AI patterns followed (healthz, metrics, NATS)

### Requesting Changes

If a commit isn't atomic:

```
"This commit does multiple things:
1. Adds the new feature
2. Refactors existing code
3. Updates documentation

Please split into separate PRs for easier review."
```

---

## Related Documentation

- [CONTRIBUTING.md](../CONTRIBUTING.md) - General contribution guidelines
- [SUBMODULE_WORKFLOW.md](SUBMODULE_WORKFLOW.md) - Submodule Git workflow
- [SUBMODULE_INTEGRATION_CHECKLIST.md](SUBMODULE_INTEGRATION_CHECKLIST.md) - Integration checklist
- [CHIT_V2_SPECIFICATION.md](CHIT_V2_SPECIFICATION.md) - CHIT manifest format

---

**Maintainer:** PMOVES.AI Team
