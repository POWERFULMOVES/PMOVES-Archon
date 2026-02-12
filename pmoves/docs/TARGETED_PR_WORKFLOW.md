# Targeted PR Workflow for PMOVES.AI

**Purpose:** Define guidelines for creating focused, reviewable pull requests in PMOVES.AI development.

**Last Updated:** 2026-02-12

---

## Overview

Targeted PRs are smaller, focused pull requests that address a **single concern** and can be reviewed thoroughly in a single session. This contrasts with monolithic "mega-PRs" that combine multiple unrelated changes.

```
One PR Scope = One Reviewable Unit
```

### Benefits

- **Faster Reviews:** Smaller PRs can be reviewed in 15-30 minutes
- **Better Quality:** More eyes on each change
- **Safer Merges:** Less risk of unintended side effects
- **Easier Reverts:** Clean revert history if needed
- **PMOVES.AI Aware:** PRs respect service boundaries and integration patterns

---

## PR Categories

### 1. Feature PRs (`feat`)

**Purpose:** Add new functionality

**Scope:**
- Single feature or endpoint
- Related tests included
- Documentation updated

**Example Title:** `feat(agent-zero): Add MCP service discovery endpoint`

**Size Limits:**
- Files: ≤ 15
- Lines changed: ≤ 400
- Services affected: 1

**Checklist:**
- [ ] Feature implementation complete
- [ ] Unit tests added/updated
- [ ] Integration tests added
- [ ] Documentation updated (README, API docs)
- [ ] CHIT manifest updated (if new service)
- [ ] Health check passes (`/healthz`)
- [ ] Metrics endpoint verified (`/metrics`)

---

### 2. Bug Fix PRs (`fix`)

**Purpose:** Resolve reported issues

**Scope:**
- Single bug or regression
- Reproduction case addressed
- Test case added to prevent recurrence

**Example Title:** `fix(hirag): Handle empty query results without error`

**Size Limits:**
- Files: ≤ 5
- Lines changed: ≤ 100
- Services affected: 1

**Checklist:**
- [ ] Bug root cause identified
- [ ] Fix implemented and tested
- [ ] Regression test added
- [ ] Related documentation updated
- [ ] Issue referenced in commit/PR

---

### 3. Refactoring PRs (`refactor`)

**Purpose:** Improve code structure without behavior changes

**Scope:**
- Single module or service
- No external behavior changes
- Tests updated (if needed)

**Example Title:** `refactor(registry): Simplify service lookup with caching`

**Size Limits:**
- Files: ≤ 20
- Lines changed: ≤ 500
- Services affected: 1-2

**Checklist:**
- [ ] Refactoring complete
- [ ] All existing tests pass
- [ ] No new behavior introduced
- [ ] Performance not degraded
- [ ] Code review completed

---

### 4. Documentation PRs (`docs`)

**Purpose:** Update project documentation

**Scope:**
- Single documentation topic
- Related docs updated together
- No code changes (unless necessary)

**Example Title:** `docs(submodules): Add PMOVES-NewService to catalog`

**Size Limits:**
- Files: ≤ 10
- Lines changed: N/A (focus on completeness)

**Checklist:**
- [ ] Documentation complete and accurate
- [ ] All references updated
- [ ] Examples tested (if applicable)
- [ ] Internal links verified
- [ ] Typos/grammar checked

---

### 5. Submodule Update PRs (`chore`)

**Purpose:** Update submodule references or sync changes

**Scope:**
- Single submodule or related group
- Version bump clear
- Parent updates minimal

**Example Title:** `chore(submodules): Update Agent-Zero to abc123d`

**Size Limits:**
- Files: ≤ 3 (submodule ref + related docs)
- Lines changed: ≤ 50
- Services affected: N/A (parent repo only)

**Checklist:**
- [ ] Submodule on correct branch
- [ ] Commit SHA verified
- [ ] SUBMODULE_LIST.md updated
- [ ] Related docs updated
- [ ] CI builds passing

---

## PR Structure by Service Tier

### API Tier PRs

Services: Agent Zero, Archon, BoTZ Gateway, TensorZero

**Focus:** HTTP endpoints, API contracts

**Review Priorities:**
1. API contract correctness
2. Request/response validation
3. Error handling
4. Rate limiting (if applicable)

**Example PR:**
```
feat(agent-zero): Add MCP tool execution endpoint

POST /mcp/execute
- Validates tool requests
- Executes via embedded agent
- Returns execution results
- Includes integration tests
```

---

### LLM Tier PRs

Services: TensorZero, model providers

**Focus:** Model routing, observability, token tracking

**Review Priorities:**
1. Model provider integration
2. Observability (ClickHouse)
3. Rate limiting
4. Fallback behavior

**Example PR:**
```
fix(tensorzero): Retry on model provider timeout

- Adds exponential backoff
- Logs retries to ClickHouse
- Fails gracefully after 3 attempts
```

---

### Worker Tier PRs

Services: Extract Worker, LangExtract, media analyzers

**Focus:** Job processing, reliability

**Review Priorities:**
1. Job queue handling
2. Error recovery
3. Resource cleanup
4. Idempotency

**Example PR:**
```
fix(extract): Handle concurrent indexing requests

- Adds request deduplication
- Returns cached result for in-flight jobs
- Reduces Qdrant load
```

---

### Media Tier PRs

Services: Ultimate-TTS-Studio, FFmpeg-Whisper, media analyzers

**Focus:** GPU utilization, processing pipelines

**Review Priorities:**
1. GPU memory management
2. Processing reliability
3. Output quality
4. Resource cleanup

**Example PR:**
```
perf(whisper): Optimize GPU memory usage

- Reduces batch size for large files
- Clears CUDA cache between jobs
- Improves throughput by 40%
```

---

### Data Tier PRs

Services: Supabase, Qdrant, Neo4j, Meilisearch

**Focus:** Data integrity, migrations

**Review Priorities:**
1. Migration safety
2. Data consistency
3. Backup/restore paths
4. Index maintenance

**Example PR:**
```
feat(supabase): Add agent state table

- Migration file: 20260212_add_agent_state.sql
- Upsert pattern for state updates
- Includes rollback migration
```

---

## PR Template

```markdown
## Summary
<!-- Brief description of what this PR does and why -->

## Changes
<!-- List of files/areas modified -->

## Testing
<!-- How this was tested -->

## PMOVES.AI Integration
<!-- For service PRs: integration points -->
- [ ] Service announcement on NATS (`services.announce.v1`)
- [ ] Health check endpoint (`/healthz`)
- [ ] Metrics endpoint (`/metrics`)
- [ ] CHIT manifest updated
- [ ] Environment variables documented

## Related Issues
<!-- Fixes #xxx, Related to #yyy -->

## Checklist
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Ready for review
```

---

## PR Review Guidelines

### For Reviewers

**Review Focus by PR Type:**

| PR Type | Focus Areas |
|-----------|-------------|
| Feature | Correctness, completeness, integration |
| Bug Fix | Root cause, test coverage, regression |
| Refactor | Simplicity, maintainability, tests |
| Docs | Accuracy, completeness, examples |
| Chore | Necessity, correct process |

### Review Comments

**Constructive Feedback Pattern:**

```markdown
# Suggestion

## Issue
The current implementation doesn't handle empty results.

## Suggested Fix
Add a check for empty array before processing:
```python
if not results:
    return empty_response()
```

## Why
This prevents errors downstream and provides clearer API contract.
```

### Requesting Changes

**When to Request Changes:**
- Security vulnerabilities
- Breaking API changes
- Missing error cases
- Performance regressions
- Integration issues

**When to Suggest (Optional):**
- Code style improvements
- Additional test cases
- Documentation clarity
- Minor optimizations

---

## PR Merging Strategy

### Merge Method

PMOVES.AI uses **Squash and Merge** for most PRs:

```bash
# Maintainer action
gh pr merge <pr-number> --squash --subject "feat(service): Add feature"
```

**Why Squash:**
- Clean commit history
- PR title as final commit message
- Eliminates "fix typo" and "WIP" commits

### Fast-Forward Exceptions

Use **Fast-Forward** for:
- Hotfixes to production
- Documentation typo fixes
- Trivial CI fixes

```bash
gh pr merge <pr-number> --ff
```

---

## Anti-Patterns to Avoid

### The Mega-PR

**Bad:**
```markdown
## Summary
This PR adds:
- New service discovery
- Updated documentation
- Fixed 3 bugs in Archon
- Refactored health checks
- Added integration tests
- Updated Docker configs
```

**Fix:** Split into 5-6 focused PRs

### The Mixed-Purpose PR

**Bad:**
```
feat: Add feature and fix unrelated bug
```

**Fix:** Remove bug fix, file separately

### The Surprise Dependency

**Bad:** PR requires changes to 5+ services to work

**Fix:** Add feature flags or phase integration

---

## CI/CD Integration

### PR Checks

All PMOVES.AI PRs must pass:

1. **CodeQL** - Security scanning
2. **CHIT Contract** - Schema validation
3. **SQL Policy** - Migration validation
4. **Tests** - Unit + integration
5. **Docs Build** - Documentation builds

### Status Checks

```yaml
# .github/workflows/pr-checks.yml
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Check PR size
        run: |
          FILES=$(gh pr view ${{ github.event.pull_request.number }} --json | jq '.files | length')
          if [ $FILES -gt 15 ]; then
            echo "::warning::PR has $FILES files (consider splitting)"
          fi
```

---

## Related Documentation

- [ATOMIC_COMMIT_WORKFLOW.md](ATOMIC_COMMIT_WORKFLOW.md) - Atomic commit guidelines
- [CONTRIBUTING.md](../CONTRIBUTING.md) - General contribution guidelines
- [SUBMODULE_WORKFLOW.md](SUBMODULE_WORKFLOW.md) - Submodule Git workflow
- [TESTING_STRATEGY.md](../.claude/context/testing-strategy.md) - Testing requirements

---

**Maintainer:** PMOVES.AI Team
