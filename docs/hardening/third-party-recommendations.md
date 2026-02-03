# Third-Party Service Hardening Recommendations

**Purpose:** Document security hardening recommendations for third-party services used in PMOVES.AI that we don't directly control.

**Last Updated:** 2026-01-31
**Status:** Active Recommendations

---

## Overview

PMOVES.AI uses several third-party services that cannot be directly modified because they are consumed as external images. This document provides recommended hardening configurations via Docker Compose overrides and environment variables.

---

## TensorZero Services

### TensorZero Gateway
**Image:** `ghcr.io/tensorzero/tensorzero:latest`
**Purpose:** LLM gateway and model routing
**Default Port:** 3000
**Container:** `tensorzero-gateway`

**Current Status:** Runs as root, no resource limits

**Recommendations:**

```yaml
# Add to docker-compose.hardened.yml
tensorzero-gateway:
  user: "65532:65532"  # If image supports non-root
  security_opt:
    - no-new-privileges:true
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: '1.0'
      reservations:
        memory: 128M
        cpus: '0.25'
```

**Notes:**
- Upstream repository: https://github.com/tensorzero/tensorzero
- Open issue requesting non-root image support
- Gateway proxy mode reduces blast radius

### TensorZero ClickHouse
**Image:** `clickhouse/clickhouse-server:latest`
**Purpose:** Metrics and observability storage
**Default Port:** 8123 (HTTP), 9000 (Native)
**Container:** `tensorzero-clickhouse`

**Current Status:** Runs as clickhouse user (UID 101), no resource limits

**Recommendations:**

```yaml
tensorzero-clickhouse:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '2.0'
      reservations:
        memory: 1G
        cpus: '0.5'
```

**Notes:**
- ClickHouse already runs as non-root user
- Requires significant memory for query processing
- Consider disk encryption for metrics data

### TensorZero UI
**Image:** `ghcr.io/tensorzero/tensorzero-ui:latest`
**Purpose:** Metrics dashboard
**Default Port:** 4000
**Container:** `tensorzero-ui`

**Recommendations:**

```yaml
tensorzero-ui:
  deploy:
    resources:
      limits:
        memory: 256M
        cpus: '0.5'
      reservations:
        memory: 64M
        cpus: '0.1'
```

---

## Database Services

### Qdrant (Vector Database)
**Image:** `qdrant/qdrant:latest`
**Purpose:** Vector embeddings for semantic search
**Default Port:** 6333 (HTTP), 6334 (gRPC)
**Container:** `qdrant`

**Current Status:** Runs as non-root, minimal configuration

**Recommendations:**

```yaml
qdrant:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '2.0'
      reservations:
        memory: 512M
        cpus: '0.5'
  environment:
    - QDRANT__SERVICE__MAX_REQUEST_SIZE_MB=64
    - QDRANT__STORAGE__PERFORMANCE__MAX_OPTIMIZATION_THREADS=2
```

**Security Notes:**
- Enable API key authentication: `QDRANT__SERVICE__API_KEY`
- Use TLS for production deployments
- Consider network isolation (data tier only)

### Meilisearch (Full-Text Search)
**Image:** `getmeili/meilisearch:latest`
**Purpose:** Keyword and typo-tolerant search
**Default Port:** 7700
**Container:** `meilisearch`

**Recommendations:**

```yaml
meilisearch:
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '1.0'
      reservations:
        memory: 256M
        cpus: '0.25'
  environment:
    - MEILI_MASTER_KEY=${MEILI_MASTER_KEY}  # REQUIRED
    - MEILI_ENV=production
```

**Critical Security:**
- **ALWAYS set MEILI_MASTER_KEY** - service runs without auth by default
- Rotate master key periodically
- Use strong 32+ character random keys

### Neo4j (Graph Database)
**Image:** `neo4j:5-community`
**Purpose:** Knowledge graph and relationships
**Default Ports:** 7474 (HTTP), 7687 (Bolt)
**Container:** `neo4j`

**Recommendations:**

```yaml
neo4j:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '2.0'
      reservations:
        memory: 512M
        cpus: '0.5'
  environment:
    - NEO4J_AUTH=${NEO4J_AUTH}  # username/password
    - NEO4J_dbms_memory_heap_max__size=1G
```

**Security Notes:**
- **NEVER run without authentication** (default: neo4j/neo4j)
- Enable TLS for Bolt protocol in production
- Restrict to data tier network

### PostgreSQL (via Supabase)
**Image:** `supabase/postgres:15.1.0.147`
**Purpose:** Primary metadata database
**Default Port:** 5432
**Container:** `db`

**Recommendations:**

```yaml
db:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '2.0'
      reservations:
        memory: 512M
        cpus: '0.5'
  environment:
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}  # STRONG PASSWORD
```

---

## Message Bus

### NATS (JetStream)
**Image:** `nats:latest`
**Purpose:** Event-driven message bus
**Default Ports:** 4222 (client), 8222 (monitoring)
**Container:** `nats`

**Current Status:** Runs as non-root, minimal configuration

**Recommendations:**

```yaml
nats:
  user: "65532:65532"
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: '1.0'
      reservations:
        memory: 128M
        cpus: '0.25'
  command: >
    --jetstream
    --mbed 8222
    --sd /data/jetstream
    --user pmoves
    --pass ${NATS_PASSWORD}
```

**Security Notes:**
- Use strong passwords for authentication
- Enable TLS for production
- Consider account-based auth for multi-service isolation

---

## Storage

### MinIO (S3-Compatible Storage)
**Image:** `quay.io/minio/minio:latest`
**Purpose:** Object storage for media, documents, artifacts
**Default Ports:** 9000 (API), 9001 (Console)
**Container:** `minio`

**Recommendations:**

```yaml
minio:
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '1.0'
      reservations:
        memory: 256M
        cpus: '0.25'
  environment:
    - MINIO_ROOT_USER=${MINIO_ROOT_USER}  # NOT 'minioadmin'
    - MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}  # STRONG PASSWORD
  command: server /data --console-address ":9001"
```

**Critical Security:**
- **Change default credentials** - minioadmin/minioadmin is a common target
- Use strong random passwords (32+ characters)
- Enable bucket policies for least privilege access
- Consider TLS for production

---

## Observability Stack

### Prometheus
**Image:** `prom/prometheus:latest`
**Purpose:** Metrics collection and storage
**Default Port:** 9090
**Container:** `prometheus`

**Recommendations:**

```yaml
prometheus:
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '1.0'
      reservations:
        memory: 256M
        cpus: '0.25'
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--web.console.libraries=/etc/prometheus/console_libraries'
    - '--web.console.templates=/etc/prometheus/consoles'
    - '--storage.tsdb.retention.time=15d'
```

### Grafana
**Image:** `grafana/grafana:latest`
**Purpose:** Metrics visualization and dashboards
**Default Port:** 3000
**Container:** `grafana`

**Recommendations:**

```yaml
grafana:
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: '0.5'
      reservations:
        memory: 128M
        cpus: '0.1'
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}  # CHANGE DEFAULT
    - GF_INSTALL_PLUGINS=
```

**Security Notes:**
- Change default admin password (admin/admin)
- Disable anonymous access in production
- Use strong passwords for data source connections

### Loki
**Image:** `grafana/loki:latest`
**Purpose:** Log aggregation
**Default Port:** 3100
**Container:** `loki`

**Recommendations:**

```yaml
loki:
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '1.0'
      reservations:
        memory: 256M
        cpus: '0.25'
```

---

## Media Processing

### Ollama (Local LLM Inference)
**Image:** `ollama/ollama:latest`
**Purpose:** Local model inference
**Default Port:** 11434
**Container:** `ollama`

**Recommendations:**

```yaml
ollama:
  deploy:
    resources:
      limits:
        memory: 8G  # Adjust based on model size
        cpus: '4.0'
      reservations:
        memory: 2G
        cpus: '1.0'
  environment:
    - OLLAMA_HOST=0.0.0.0
```

**Notes:**
- Requires GPU for optimal performance
- Memory requirements vary by model
- Restrict to internal network

---

## Special Cases

### cAdvisor (Container Metrics)
**Image:** `gcr.io/cadvisor/cadvisor:latest`
**Purpose:** Container resource monitoring
**Default Port:** 8080
**Container:** `cadvisor`

**Security Issue:** Requires `privileged: true` for container metrics

**Recommendations:**

```yaml
cadvisor:
  devices:
    - /dev/kmsg
  privileged: true  # REQUIRED - no alternative
  deploy:
    resources:
      limits:
        memory: 256M
        cpus: '0.5'
      reservations:
        memory: 64M
        cpus: '0.1'
  networks:
    - pmoves_monitoring  # RESTRICT to monitoring network only
```

**Mitigation:**
- Run on monitoring network only
- Restrict metrics exposure
- Consider alternative: Docker stats API directly

---

## Implementation Priority

| Service | Priority | Action Required |
|---------|----------|-----------------|
| Meilisearch | **P0** | Set MEILI_MASTER_KEY |
| MinIO | **P0** | Change default credentials |
| Grafana | **P0** | Change admin password |
| Neo4j | **P0** | Enable authentication |
| TensorZero Services | **P1** | Add resource limits |
| Database Services | **P1** | Add resource limits |
| cAdvisor | **P2** | Network restrict only |

---

## Validation Checklist

Before deploying to production:

- [ ] All default passwords changed
- [ ] API keys configured for all services
- [ ] Resource limits defined for all services
- [ ] TLS enabled for external-facing services
- [ ] Network segregation enforced (data tier isolation)
- [ ] Monitoring and alerting configured
- [ ] Backup strategy implemented
- [ ] Secret rotation policy documented

---

## References

- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [NIST Container Security Guidelines](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf)
- [OWASP Docker Top 10](https://owasp.org/www-project-docker-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
