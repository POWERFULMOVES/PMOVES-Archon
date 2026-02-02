# GHCR Namespace Publishing for PMOVES.AI

**Status:** Documented
**Last Updated:** 2026-01-29
**Purpose:** Docker image publishing with lowercase namespace normalization

---

## Overview

GitHub Container Registry (GHCR) **requires lowercase namespaces** for image references. This document explains how PMOVES.AI handles namespace normalization during CI/CD builds.

**Problem:** GitHub organization names can be mixed-case (e.g., `POWERFULMOVES`), but GHCR only accepts lowercase.

**Solution:** Normalize the repository owner to lowercase in all CI/CD pipelines.

## Namespace Normalization

### GitHub Actions

```yaml
# .github/workflows/docker-build.yml
name: Build and Push to GHCR

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:

permissions:
  contents: read
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Normalize and Build
        run: |
          # CRITICAL: Normalize org name to lowercase
          ORG=$(echo '${{ github.repository_owner }}' | tr '[:upper:]' '[:lower:]')
          REPO=${{ github.event.repository.name }}
          SHA=${{ github.sha }}

          # Build with normalized namespace
          docker buildx build \
            --platform linux/amd64,linux/arm64 \
            --tag ghcr.io/${ORG}/${REPO}:${SHA} \
            --tag ghcr.io/${ORG}/${REPO}:latest \
            --push \
            .

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ghcr.io/${{ steps.normalize.outputs.org }}/${{ github.event.repository.name }}:${{ github.sha }}
            ghcr.io/${{ steps.normalize.outputs.org }}/${{ github.event.repository.name }}:latest
```

### Using Build Arguments

```yaml
      - name: Build with org as arg
        run: |
          ORG=$(echo '${{ github.repository_owner }}' | tr '[:upper:]' '[:lower:]')
          docker buildx build \
            --build-arg ORG=${ORG} \
            --tag ghcr.io/${ORG}/app:${{ github.sha }} \
            --push \
            .
```

## Multi-Architecture Builds

### AMD64 and ARM64

```yaml
      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push multi-arch
        run: |
          ORG=$(echo '${{ github.repository_owner }}' | tr '[:upper:]' '[:lower:]')
          docker buildx build \
            --platform linux/amd64,linux/arm64 \
            --provenance true \
            --sbom true \
            --tag ghcr.io/${ORG}/app:${{ github.sha }} \
            --tag ghcr.io/${ORG}/app:latest \
            --push \
            .
```

## Docker Compose Integration

### Using Normalized Images

```yaml
# docker-compose.yml
services:
  example-service:
    # Use normalized namespace in production
    image: ghcr.io/powerfulmoves/app:latest
    # NOT: ghcr.io/POWERFULMOVES/app:latest (will fail)
```

### Environment Variable Reference

```yaml
# .env.production
IMAGE_REGISTRY=ghcr.io
IMAGE_ORG=powerfulmoves
IMAGE_TAG=${GIT_SHA}

# Service uses:
# ${IMAGE_REGISTRY}/${IMAGE_ORG}/app:${IMAGE_TAG}
# → ghcr.io/powerfulmoves/app:abc123
```

## Local Development

### Testing Image Pulls

```bash
# Pull from GHCR (lowercase required)
docker pull ghcr.io/powerfulmoves/tensorzero:latest

# Re-tag for local development
docker tag ghcr.io/powerfulmoves/tensorzero:latest pmoves/tensorzero:dev
```

### Authentication

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u ${GITHUB_USER} --password-stdin

# Or using GitHub CLI
gh auth token | docker login ghcr.io -u ${GITHUB_USER} --password-stdin
```

## Validation

### Verify Image Tags

```bash
# Check manifest (inspect)
docker buildx imagetools inspect ghcr.io/powerfulmoves/app:latest

# Verify platforms supported
docker buildx imagetools inspect ghcr.io/powerfulmoves/app:latest --raw | jq '.manifests[] | .platform'
```

### Test Locally

```bash
# Test pull before deploying
docker pull ghcr.io/powerfulmoves/app:latest
docker run --rm ghcr.io/powerfulmoves/app:latest --version
```

## CI/CD Patterns

### Reusable Workflow

```yaml
# .github/workflows/_build.yml
name: Build and Push

on:
  workflow_call:
    inputs:
      service:
        required: true
        type: string
      context:
        required: true
        type: string

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Normalize namespace
        id: normalize
        run: |
          ORG=$(echo '${{ github.repository_owner }}' | tr '[:upper:]' '[:lower]')
          echo "org=${ORG}" >> $GITHUB_OUTPUT

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ${{ inputs.context }}
          push: true
          tags: |
            ghcr.io/${{ steps.normalize.outputs.org }}/${{ inputs.service }}:${{ github.sha }}
            ghcr.io/${{ steps.normalize.outputs.org }}/${{ inputs.service }}:latest
```

### Caller Workflow

```yaml
# .github/workflows/build-tensorzero.yml
name: Build TensorZero

on:
  push:
    paths:
      - 'pmoves/services/tensorzero/**'

jobs:
  build:
    uses: ./.github/workflows/_build.yml
    with:
      service: tensorzero
      context: ./pmoves/services/tensorzero
```

## Troubleshooting

### Error: "manifest invalid"

**Cause:** Incorrect namespace casing

**Fix:** Ensure all image references use lowercase:
```bash
# WRONG
docker pull ghcr.io/POWERFULMOVES/app:latest

# CORRECT
docker pull ghcr.io/powerfulmoves/app:latest
```

### Error: "unauthorized: authentication required"

**Cause:** Missing or invalid GitHub token

**Fix:**
```bash
# Check token permissions
gh auth status

# Refresh token with write:packages scope
gh auth refresh -h github.com -s write:packages
```

## Related Documentation

- [Docker Hardening & Production Deployment](../PMOVES.AI%20Services%20and%20Integrations.md#docker-hardening--production-deployment)
- [GitHub Actions Self-Hosted Runner Setup](../PMOVES_Git_Organization.md#github-actions-self-hosted-runner-setup)

## External References

- [GitHub Container Registry Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Multi-Platform Builds](https://docs.docker.com/build/building/multi-platform/)
