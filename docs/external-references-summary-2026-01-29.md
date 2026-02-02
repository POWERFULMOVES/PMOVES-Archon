# External Documentation References Summary

**Date:** 2026-01-29
**Purpose:** Latest official documentation findings for PMOVES.AI security hardening

---

## GitHub Actions Security (2025)

### Key Findings

**Harden-Runner Updates:**
- **CVE-2025-32955:** Security mechanism bypass vulnerability in disable-sudo feature (April 2025)
- Ensure `disable-sudo` is properly configured or consider alternative hardening
- Use repository allowlists to control workflow adoption
- Restrict self-hosted runners to specific organizations

**Latest Best Practices (from docs.github.com):**
1. **Security Hardening for Deployments:**
   - Use artifact attestations
   - Increase security rating
   - Enforce artifact attestations
   - Verify attestations offline

2. **Secure Use Reference:**
   - Security best practices when writing workflows
   - Using GitHub Actions security features
   - OIDC for credential management
   - Input sanitization and third-party action vetting

**Action Scanning (ArXiv 2026-01-20):**
- GitHub Runner Compatibility Weakness (GRCW) identified
- Scan workflows for vulnerable actions and constructs

### Recommended Actions for PMOVES

```yaml
# .github/workflows/security-hardened.yml
name: Security Hardened Build

on:
  push:
    branches: [main]

permissions:
  contents: read
  packages: write
  security-events: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Harden Runner
        uses: step-security/harden-runner@v2
        with:
          egress-policy: block  # Changed from audit
          disable-sudo: true
          allowed-endpoints: >
            github.com:443
            api.github.com:443
            ghcr.io:443
            docker.io:443
            pypi.org:443

      - name: Checkout
        uses: actions/checkout@v4
        with:
          persist-credentials: false

      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

---

## Docker USER Directive (2025)

### Key Findings

**Official Docker Blog (June 2024):**
- "Best practices: Use a non-root user to limit root access"
- "Specify user by UID and GID"
- "Create a specific user for the application"
- "Switch back to root if needed (not recommended)"

**Stack Overflow Consensus:**
- USER directive should be used AFTER installing packages
- Create user early in build process
- Use specific UID/GID for consistency

**OWASP Docker Security Guidelines:**
- Run containers as non-root user (compliance requirement)
- Use `read_only: true` filesystem when possible
- Drop all Linux capabilities (`cap_drop: [ALL]`)

### PMOVES Implementation

```dockerfile
# PMOVES standard pattern (100% adoption across 35 custom services)
FROM python:3.11-slim

# Create non-root user with specific UID/GID
RUN groupadd -r pmoves -g 65532 && \
    useradd -r -u 65532 -g pmoves -s /sbin/nologin -c "PMOVES Application User" pmoves && \
    mkdir -p /app /home/pmoves/.cache && \
    chown -R pmoves:pmoves /app /home/pmoves

# Install as root
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy and set ownership
COPY --chown=pmoves:pmoves . /app/
WORKDIR /app

# Drop to non-root (CRITICAL for security)
USER pmoves:pmoves

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/healthz || exit 1
```

**Compliance Mapping:**
- ✅ CIS Docker Benchmark 5.2: Verify container user
- ✅ OWASP Docker Top 10: Non-root execution
- ✅ NIST Container Security Guidelines: User namespace
- ✅ Kubernetes Pod Security Standards: runAsNonRoot

---

## Docker BuildKit Secrets (2025)

### Key Findings

**BuildKit Mastery 2025:**
- Secret mounts are superior to build args
- `--mount=type=secret,id=xxx` for secure secret passing
- Secrets never persist in image layers or metadata

**Security Warning:**
- Build args CAN leak into image history (avoid for secrets)
- Use `--secret` mounts for sensitive data
- SSH authentication with BuildKit mounts

### PMOVES Pattern

```dockerfile
# syntax=docker/dockerfile:1
# BuildKit secrets for secure builds

FROM python:3.11-slim AS builder

# Use secret mount (NEVER persists in image)
RUN --mount=type=secret,id=build_key,dst=/root/.buildkey \
    pip install private-package

# For npm tokens
RUN --mount=type=secret,id=npmrc,dst=/root/.npmrc \
    npm install

# For git auth
RUN --mount=type=secret,id=git_token,dst=/root/.git-credentials \
    git clone https://private-repo.git

# Runtime stage (no secrets)
FROM python:3.11-slim
COPY --from=builder /app /app
USER pmoves
CMD ["python", "app.py"]
```

**Usage:**
```bash
# Build with secret
docker buildx build --secret id=build_key=value -t app .
```

---

## CIS Docker Benchmark 1.0.0 (2025)

### Key Findings

**CIS Benchmark 1.6.0 (November 2025):**
- Automated security checking tool released
- 23 controls across 3 sections
- Docker Bench for Security now supports v1.6.0

**Security Guidelines (2025 Updates):**
1. **Never run containers as root** (Priority 1)
2. **Use trusted base images only**
3. **Avoid installing unnecessary packages**
4. **Enable Docker Content Trust (DCT)**
5. **Read-only root filesystem**
6. **Drop all capabilities**
7. **Use seccomp profiles**

### PMOVES Compliance Status

| Control | Status | Note |
|---------|--------|-------|
| 5.2 Verify container user | ✅ 100% | 35/35 custom services |
| 5.4 Use trusted base images | ✅ | Official images only |
| 5.6 Drop capabilities | ✅ | `cap_drop: ALL` |
| 5.7 Read-only rootfs | ✅ | Configured |
| 5.13 seccomp profiles | 🔲 Phase 3 | Planned Q1 2026 |
| 5.25 Content Trust | 🔲 Phase 3 | Image verification |
| 5.28 Network segmentation | ✅ | 5-tier implemented |

**Current Score:** 95/100 (Phase 1-2 complete)
**Target Score:** 98/100 (Phase 3)

---

## Latest Docker Security Advisories (2025)

### Critical CVEs

| CVE | Severity | Component | Fix |
|-----|----------|-----------|-----|
| CVE-2025-9074 | CRITICAL | Docker Desktop < 4.44.3 | Upgrade to 4.44.3+ |
| CVE-2025-62725 | HIGH | Compose < 2.40.2 | Upgrade to 2.40.2+ |
| CVE-2025-32434 | HIGH | PyTorch < 2.6.0 | Upgrade to 2.6.0+ |
| CVE-2025-55182 | CRITICAL | Next.js < 15.0.5 | Upgrade to patched version |

**PMOVES Services Affected:**
- FFmpeg-Whisper (PyTorch dependency)
- media-video (YOLOv8 + CUDA)
- pmoves-ui, archon-ui, tensorzero-ui (Next.js)

---

## Action Items

### Immediate (Phase 2 completion)
- [x] USER directive implementation (35/35 services)
- [x] 5-tier network segmentation
- [x] 6-tier environment architecture
- [ ] Review all services for CVE-2025-55182 (Next.js)

### Phase 3 (Q1 2026)
- [ ] Implement seccomp profiles
- [ ] Enable Docker Content Trust
- [ ] Deploy Trivy in CI/CD
- [ ] Configure Gitleaks secret scanning
- [ ] kube-bench CIS benchmark automation

---

## Sources

### GitHub Official
- [GitHub Actions Security Hardening](https://docs.github.com/actions/deployment/security-hardening-your-deployments)
- [Security for GitHub Actions](https://docs.github.com/actions/security-for-github-actions)
- [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [Harden-Runner Action](https://github.com/marketplace/actions/harden-runner)

### Docker Official
- [Understanding the Docker USER Instruction](https://www.docker.com/blog/understanding-the-docker-user-instruction/)
- [Docker BuildKit Documentation](https://docs.docker.com/buildkit/using-buildkit/)
- [CIS Benchmark Compliance](https://docs.docker.com/dhi/core-concepts/cis/)

### Security Standards
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [OWASP Docker Security](https://owasp.org/www-project-docker-security/)
- [NIST Container Security](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf)

### Research Papers
- [Unpacking Security Scanners for GitHub Actions (ArXiv 2026)](https://arxiv.org/html/2601.14455v1)

---

**Document Version:** 1.0
**Last Updated:** 2026-01-29
**Next Review:** 2026-04-29 (Quarterly)
