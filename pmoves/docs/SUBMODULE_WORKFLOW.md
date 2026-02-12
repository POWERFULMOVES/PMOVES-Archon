# Submodule Workflow Documentation

**Purpose:** Document the complete workflow for adding and managing PMOVES.AI submodules.

**Last Updated:** 2026-02-12

---

## Overview

PMOVES.AI uses git submodules for component management. Each submodule is a separate repository that integrates with the parent PMOVES.AI ecosystem.

```
PMOVES.AI (parent)
├── .gitmodules          # Submodule definitions
├── pmoves/
│   ├── docs/           # Documentation
│   ├── templates/       # Submodule templates
│   └── env.shared       # Shared environment
└── PMOVES-Service/      # Submodule directories
    ├── chit/
    │   └── secrets_manifest_v2.yaml
    ├── pmoves_announcer/
    ├── pmoves_registry/
    ├── pmoves_health/
    └── pmoves_common/
```

---

## Workflow: Adding New Submodule

### Step 1: Fork Repository

```bash
# Fork upstream repository
gh repo fork upstream-user/upstream-repo --org POWERFULMOVES

# Verify fork exists
gh repo view POWERFULMOVES/PMOVES-NewService
```

### Step 2: Create Hardened Branch

```bash
# Clone your fork
git clone git@github.com:POWERFULMOVES/PMOVES-NewService.git
cd PMOVES-NewService

# Create hardened branch from main
git checkout -b PMOVES.AI-Edition-Hardened

# Push to origin
git push -u origin PMOVES.AI-Edition-Hardened
```

### Step 3: Add to Parent .gitmodules

In parent PMOVES.AI repository:

```bash
# Add submodule entry
git submodule add -b PMOVES.AI-Edition-Hardened \
  https://github.com/POWERFULMOVES/PMOVES-NewService.git \
  PMOVES-NewService

# Commit submodule addition
git commit -m "chore(submodules): Add PMOVES-NewService"
git push
```

**.gitmodules Entry:**
```gitmodules
[submodule "PMOVES-NewService"]
	path = PMOVES-NewService
	url = https://github.com/POWERFULMOVES/PMOVES-NewService.git
	branch = PMOVES.AI-Edition-Hardened
```

### Step 4: Create Integration Files

In the new submodule:

```bash
cd PMOVES-NewService

# Copy template files
cp ../pmoves/templates/submodule/chit/secrets_manifest_v2.yaml \
   chit/secrets_manifest_v2.yaml
cp ../pmoves/templates/submodule/PMOVES.AI_INTEGRATION.md \
   PMOVES.AI_INTEGRATION.md

# Copy integration packages (from existing service or create)
# - pmoves_announcer/
# - pmoves_registry/
# - pmoves_health/
# - pmoves_common/
```

### Step 5: Update Parent Repository Files

In parent PMOVES.AI:

```bash
# 1. Update SUBMODULE_LIST.md
vim pmoves/docs/SUBMODULE_LIST.md

# 2. Add service to docker-compose
vim pmoves/docker-compose.pmoves.yml

# 3. Add credentials to env.shared (if needed)
vim pmoves/env.shared

# 4. Register in CHIT manifest
vim pmoves/chit/secrets_manifest_v2.yaml

# 5. Commit all changes
git add .
git commit -m "feat(integration): Add PMOVES-NewService integration"
git push
```

### Step 6: Verify Integration

```bash
# In submodule
cd PMOVES-NewService
git branch --show-current  # Should be: PMOVES.AI-Edition-Hardened

# In parent
cd ..
git submodule status  # Should show no changes
```

---

## Workflow: Syncing Submodules

### Update Single Submodule

```bash
# In submodule directory
cd PMOVES-Service

# Pull latest changes
git fetch origin
git rebase origin/PMOVES.AI-Edition-Hardened

# Or merge if you prefer
git merge origin/PMOVES.AI-Edition-Hardened
```

### Update All Submodules

```bash
# In parent repository
git submodule update --remote --merge

# Or init new submodules
git submodule update --init --recursive
```

### Sync Nested Submodules

```bash
# Update submodules within submodules
git submodule update --recursive --remote
```

---

## Workflow: Branch Management

### Development Workflow

```
feature/* (submodule)
         │
         ▼
    [development]
         │
         ▼
      main (submodule)
         │
         ▼
    PMOVES.AI-Edition-Hardened (submodule)
         │
         ▼
    main (parent PMOVES.AI)
```

### Step-by-Step

1. **Create feature branch** in submodule
   ```bash
   cd PMOVES-Service
   git checkout -b feature/my-feature
   ```

2. **Develop and test** locally
   ```bash
   # Make changes
   git add .
   git commit -m "feat: add my feature"
   ```

3. **Merge to main** in submodule
   ```bash
   git checkout main
   git merge feature/my-feature
   git push
   ```

4. **Merge to hardened** in submodule
   ```bash
   git checkout PMOVES.AI-Edition-Hardened
   git merge main
   git push
   ```

5. **Update parent** .gitmodules
   ```bash
   cd ..
   git add PMOVES-Service
   git commit -m "chore(submodules): Update PMOVES-Service to latest hardened"
   ```

---

## Workflow: Debugging Submodules

### Check Submodule Status

```bash
# List all submodules
git submodule status

# Show submodule HEAD commits
git submodule foreach 'git log -1 --oneline'
```

### Fix Detached HEAD

```bash
# If submodule is in detached HEAD state
cd PMOVES-Service
git checkout PMOVES.AI-Edition-Hardened
```

### Reset Submodule

```bash
# Reset to current tracked version
git submodule update --force PMOVES-Service

# Or remove and re-clone
git rm --cached PMOVES-Service
rm -rf PMOVES-Service
git submodule add https://github.com/POWERFULMOVES/PMOVES-Service.git PMOVES-Service
```

---

## Workflow: CI/CD Integration

### GitHub Actions

Submodules are built and published via CI/CD:

```yaml
# .github/workflows/build.yml
name: Build and Push

on:
  push:
    branches: [PMOVES.AI-Edition-Hardened]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: recursive
      - name: Build image
        run: docker build -t ghcr.io/POWERFULMOVES/${{ github.repository }} .
```

### Multi-Architecture Builds

```yaml
strategy:
  matrix:
    platform: [linux-amd64, linux-arm64]
steps:
  - name: Build for ${{ matrix.platform }}
    run: docker build --platform ${{ matrix.platform }} .
```

---

## Troubleshooting

### Submodule Not Updating

**Problem:** `git submodule update` shows no changes but submodule is outdated.

**Solution:**
```bash
# Force refresh from remote
git submodule update --remote --merge

# Or manually
cd PMOVES-Service
git fetch origin
git checkout origin/PMOVES.AI-Edition-Hardened
```

### Wrong Branch

**Problem:** Submodule is on wrong branch.

**Solution:**
```bash
cd PMOVES-Service
git checkout PMOVES.AI-Edition-Hardened
git branch --set-upstream-to=origin/PMOVES.AI-Edition-Hardened
```

### Nested Submodule Issues

**Problem:** Nested submodule not updating.

**Solution:**
```bash
# Update recursively
git submodule update --recursive --remote

# Or update specific nested submodule
cd PMOVES-Service/NestedSubmodule
git pull origin PMOVES.AI-Edition-Hardened
```

### Merge Conflicts

**Problem:** Merge conflict in submodule.

**Solution:**
```bash
cd PMOVES-Service
git fetch origin
git rebase origin/PMOVES.AI-Edition-Hardened

# Resolve conflicts
# Edit files
git add .
git rebase --continue
```

---

## Best Practices

### Commit Messages

Use conventional commits for consistency:

```
feat: add new feature
fix: bug fix
chore: maintenance task
docs: documentation
test: add tests
refactor: code refactoring
perf: performance improvement
ci: CI/CD changes
```

### Branch Naming

- `feature/*` - New features
- `fix/*` - Bug fixes
- `chore/*` - Maintenance
- `docs/*` - Documentation
- `test/*` - Test changes

### Before Committing

1. Run tests: `pytest` / `npm test`
2. Check linting: `ruff check` / `npm run lint`
3. Verify integration: `docker compose up`
4. Update documentation

### Submodule Hygiene

- Always commit submodule changes before pushing parent
- Keep submodules on `PMOVES.AI-Edition-Hardened` branch
- Update `.gitmodules` consistently
- Document new submodules in `SUBMODULE_LIST.md`

---

## Related Documentation

- [SUBMODULE_LIST.md](SUBMODULE_LIST.md) - Complete submodule catalog
- [PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md](PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md) - Integration guide
- [SUBMODULE_ARCHITECTURE.md](SUBMODULE_ARCHITECTURE.md) - Architecture details
- [SUBMODULE_COMMIT_REVIEW_2026-02-07.md](SUBMODULE_COMMIT_REVIEW_2026-02-07.md) - Commit tracking

---

**Maintainer:** PMOVES.AI Team
