# CHIT v2 Manifest Specification

**Purpose:** Define the CHIT v2 secrets manifest format for PMOVES.AI services.

**Last Updated:** 2026-02-12

---

## Overview

CHIT v2 (Compressed Hierarchical Information Transfer) is PMOVES.AI's secret management system. The `secrets_manifest_v2.yaml` file defines a service's secret requirements, sources, and validation rules.

**Location:** `chit/secrets_manifest_v2.yaml` in each service directory

---

## Manifest Structure

```yaml
# PMOVES.AI CHIT Secrets Manifest
api_version: "2.0"

environment: ${CHIT_ENVIRONMENT:-production}

# Secrets sources in precedence order (higher number = higher precedence)
sources:
  - type: env
    precedence: 50
  - type: chit_vault
    precedence: 100
  - type: docker_secret
    precedence: 75
  - type: github_secret
    precedence: 25

# Service Identity (REQUIRED)
service_slug: "your-service-slug"
name: "Your Service Name"
version: "1.0.0"
description: "Description of your service"

# Ports exposed by this service
ports:
  - name: main
    port: 8080
    protocol: http
  - name: metrics
    port: 9090
    protocol: http

# Secrets required by this service
secrets:
  - name: YOUR_SERVICE_API_KEY
    description: "API key for external service access"
    required: true
    category: credentials
    source: env
    default_value: ""

# Service configuration variables
variables:
  SERVICE_NAME: ~
  SERVICE_SLUG: ~
  NATS_URL: ~
  LOG_LEVEL: ~

# Environment groups
groups:
  development:
    required:
      - SERVICE_NAME
      - NATS_URL
    optional:
      - LOG_LEVEL
  production:
    required:
      - SERVICE_NAME
      - SERVICE_SLUG
      - NATS_URL
    optional:
      - LOG_LEVEL

# Container definitions
containers:
  - name: main
    image: ghcr.io/POWERFULMOVES/service-slug:latest
    environment:
      - YOUR_SERVICE_API_KEY=${YOUR_SERVICE_API_KEY}
      - NATS_URL=${NATS_URL}
    secrets:
      - your_service_api_key

# Validation rules
validation:
  strict: false
  fail_on_missing_required: true

# Service registration for discovery
groups:
  - name: tier
    services:
      - your-service-slug
    description: "Your Service"
    tier: "worker"  # agent, llm, data, api, media
```

---

## Field Reference

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|-----------|-------------|
| `api_version` | string | Yes | Manifest format version (must be "2.0") |
| `environment` | string | No | Environment name (default: production) |
| `sources` | array | No | Secret sources with precedence |
| `service_slug` | string | Yes | Unique service identifier |
| `name` | string | Yes | Human-readable service name |
| `version` | string | Yes | Service version |
| `description` | string | Yes | Service description |
| `ports` | array | No | Ports exposed by service |
| `secrets` | array | Yes | Secrets required by service |
| `variables` | object | No | Configuration variables |
| `groups` | object | No | Environment variable groups |
| `containers` | array | No | Container definitions |
| `validation` | object | No | Validation rules |

### Secret Sources

| Type | Precedence | Description |
|-------|-----------|-------------|
| `env` | 50 | Environment variables |
| `chit_vault` | 100 | CHIT Vault (highest precedence) |
| `docker_secret` | 75 | Docker secrets |
| `github_secret` | 25 | GitHub secrets |

### Service Tiers

| Tier | Description |
|-------|-------------|
| `agent` | Agent orchestration services |
| `llm` | LLM gateway services |
| `data` | Data storage services |
| `api` | API gateway services |
| `worker` | Background worker services |
| `media` | Media processing services |

---

## Secret Definition

### Basic Secret

```yaml
secrets:
  - name: MY_API_KEY
    description: "API key for external service"
    required: true
    category: credentials
    source: env
    default_value: ""
```

### CHIT Vault Secret

```yaml
secrets:
  - name: MY_SECRET_PASSWORD
    description: "Database password"
    required: true
    category: credentials
    source: chit_vault
    chit_vault:
      path: secrets/my-service/db_password
      required: true
      template: "your-db-password-here"
```

### Docker Secret

```yaml
secrets:
  - name: MY_DOCKER_SECRET
    description: "Secret from Docker"
    required: true
    category: credentials
    source: docker_secret
    docker_secret:
      path: /run/secrets/my_docker_secret
```

### Git Crypt Secret

```yaml
secrets:
  - name: MY_GIT_CRYPT_KEY
    description: "Fallback encryption key"
    required: false
    category: credentials
    source: git_crypt
    git_crypt:
      path: secrets/my-service/git_crypt_key
      template: "your-git-crypt-key-here"
```

---

## Variable Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `SERVICE_NAME` | Service name | `My Service` |
| `SERVICE_SLUG` | Service identifier | `my-service` |
| `NATS_URL` | NATS message bus | `nats://nats:4222` |
| `TENSORZERO_URL` | LLM gateway | `http://tensorzero:3030` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

---

## Container Definition

```yaml
containers:
  - name: main
    image: ghcr.io/POWERFULMOVES/my-service:latest
    ports:
      - "8080:8080"
    environment:
      - SERVICE_NAME=${SERVICE_NAME}
      - NATS_URL=${NATS_URL}
    secrets:
      - my_service_api_key
    volumes:
      - ./data:/data
```

---

## Environment Groups

### Development Group

```yaml
groups:
  development:
    required:
      - SERVICE_NAME
      - NATS_URL
      - LOG_LEVEL
    optional:
      - DEBUG_MODE
```

### Production Group

```yaml
groups:
  production:
    required:
      - SERVICE_NAME
      - SERVICE_SLUG
      - NATS_URL
      - API_KEY
    optional:
      - LOG_LEVEL
      - METRICS_ENABLED
```

---

## Validation Rules

```yaml
validation:
  strict: false  # Fail on validation errors
  fail_on_missing_required: true  # Fail if required secrets missing
  fail_on_unknown_secrets: false  # Allow undeclared secrets
```

---

## Template Variables

CHIT v2 supports template variable substitution:

| Variable | Description |
|----------|-------------|
| `${CHIT_ENVIRONMENT:-production}` | Environment name |
| `${SECRET_NAME}` | Secret value substitution |
| `${DEFAULT_VALUE:-value}` | Default value |

---

## Common Patterns

### Database Connection

```yaml
secrets:
  - name: DATABASE_URL
    description: "Database connection URL"
    required: true
    category: credentials
    source: env
    default_value: ""

  - name: DATABASE_PASSWORD
    description: "Database password"
    required: true
    category: credentials
    source: chit_vault
    chit_vault:
      path: secrets/my-service/db_password
      template: "change-me-in-production"
```

### API Keys

```yaml
secrets:
  - name: OPENAI_API_KEY
    description: "OpenAI API key for LLM access"
    required: true
    category: llm_provider
    source: chit_vault
    chit_vault:
      path: secrets/llm/openai_api_key
      template: "sk-..."

  - name: ANTHROPIC_API_KEY
    description: "Anthropic API key"
    required: true
    category: llm_provider
    source: chit_vault
    chit_vault:
      path: secrets/llm/anthropic_api_key
      template: "sk-ant-..."
```

### Service Credentials

```yaml
secrets:
  - name: SERVICE_API_URL
    description: "External service API URL"
    required: true
    category: configuration
    source: env
    default_value: "https://api.service.com"

  - name: SERVICE_API_TOKEN
    description: "External service auth token"
    required: true
    category: credentials
    source: chit_vault
    chit_vault:
      path: secrets/services/service_api_token
      template: "your-token-here"
```

---

## Example: Complete Manifest

```yaml
# PMOVES.AI CHIT Secrets Manifest
api_version: "2.0"

environment: ${CHIT_ENVIRONMENT:-production}

sources:
  - type: env
    precedence: 50
  - type: chit_vault
    precedence: 100
  - type: docker_secret
    precedence: 75

service_slug: "hirag-v2"
name: "Hi-RAG Gateway v2"
version: "1.0.0"
description: "Hybrid RAG combining vector, graph, and full-text search"

ports:
  - name: main
    port: 8086
    protocol: http
  - name: gpu
    port: 8087
    protocol: http

secrets:
  - name: QDRANT_URL
    description: "Qdrant vector database URL"
    required: true
    category: credentials
    source: env
    default_value: "http://qdrant:6333"

  - name: NEO4J_URL
    description: "Neo4j graph database URL"
    required: true
    category: credentials
    source: env
    default_value: "http://neo4j:7474"

  - name: MEILISEARCH_URL
    description: "Meilisearch full-text search URL"
    required: true
    category: credentials
    source: env
    default_value: "http://meilisearch:7700"

  - name: TENSORZERO_URL
    description: "LLM gateway for embeddings"
    required: true
    category: configuration
    source: env
    default_value: "http://tensorzero:3030"

variables:
  SERVICE_NAME: ~
  SERVICE_SLUG: ~
  NATS_URL: ~
  LOG_LEVEL: INFO
  RERANK_ENABLED: "true"

groups:
  development:
    required:
      - SERVICE_NAME
      - QDRANT_URL
      - NEO4J_URL
      - MEILISEARCH_URL
    optional:
      - LOG_LEVEL
      - RERANK_ENABLED
  production:
    required:
      - SERVICE_NAME
      - SERVICE_SLUG
      - QDRANT_URL
      - NEO4J_URL
      - MEILISEARCH_URL
      - TENSORZERO_URL
      - NATS_URL
    optional:
      - LOG_LEVEL
      - RERANK_ENABLED

containers:
  - name: main
    image: ghcr.io/POWERFULMOVES/hirag-v2:latest
    environment:
      - QDRANT_URL=${QDRANT_URL}
      - NEO4J_URL=${NEO4J_URL}
      - MEILISEARCH_URL=${MEILISEARCH_URL}
      - TENSORZERO_URL=${TENSORZERO_URL}
      - NATS_URL=${NATS_URL}
      - RERANK_ENABLED=${RERANK_ENABLED}
    ports:
      - "8086:8086"

validation:
  strict: false
  fail_on_missing_required: true

groups:
  - name: tier
    services:
      - hirag-v2
    description: "Hi-RAG Gateway v2"
    tier: "api"
```

---

## Template File

A template file is available at:
```
pmoves/templates/submodule/chit/secrets_manifest_v2.yaml
```

Copy this template to your new service directory and customize:

```bash
cp pmoves/templates/submodule/chit/secrets_manifest_v2.yaml \
   PMOVES-NewService/chit/secrets_manifest_v2.yaml
```

---

## Related Documentation

- [PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md](PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md) - Integration guide
- [SUBMODULE_LIST.md](SUBMODULE_LIST.md) - Submodule catalog
- [SECRETS_ONBOARDING.md](SECRETS_ONBOARDING.md) - Secret onboarding guide

---

**Maintainer:** PMOVES.AI Team
