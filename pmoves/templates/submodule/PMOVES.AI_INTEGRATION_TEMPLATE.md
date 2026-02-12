# PMOVES.AI Integration Documentation Template

**Copy this template to your service root directory and customize:**

```
PMOVES-YourService/PMOVES.AI_INTEGRATION.md
```

---

# PMOVES.AI Integration: [Your Service Name]

**Service Slug:** `your-service-slug`

**Integration Status:** ✅ Integrated | 🔄 In Progress | ⚠️ Not Started

**Last Updated:** YYYY-MM-DD

---

## Overview

Brief description of your service and how it integrates with PMOVES.AI ecosystem.

**Example:**
> MyService is a specialized widget processor that integrates with PMOVES.AI to provide widget analysis capabilities. It exposes FastAPI endpoints for widget processing and publishes results to NATS for downstream consumption.

---

## Service Details

| Field | Value |
|-------|-------|
| **Name** | Your Service Name |
| **Slug** | `your-service-slug` |
| **Version** | 1.0.0 |
| **Tier** | api / agent / worker / media / llm / data |
| **Language** | Python 3.11+ / Node.js / etc. |
| **Repository** | https://github.com/POWERFULMOVES/PMOVES-YourService |

---

## Ports

| Port | Protocol | Purpose |
|-------|-----------|---------|
| 8080 | HTTP | Main API |
| 9090 | HTTP | Prometheus metrics |

**Health Endpoint:** `http://your-service-slug:8080/healthz`

---

## Required Environment Variables

### Infrastructure

| Variable | Description | Default | Required |
|----------|-------------|----------|-----------|
| `NATS_URL` | NATS message bus URL | `nats://nats:4222` | Yes |
| `TENSORZERO_URL` | LLM gateway URL | `http://tensorzero:3030` | Yes |
| `LOG_LEVEL` | Logging verbosity | `INFO` | No |

### Service-Specific

| Variable | Description | Default | Required |
|----------|-------------|----------|-----------|
| `YOUR_SERVICE_API_KEY` | API key for external service | | Yes |
| `YOUR_SERVICE_CONFIG` | Service configuration | `{}` | No |

---

## Secrets

See `chit/secrets_manifest_v2.yaml` for complete secret definition.

**Required Secrets:**
- `YOUR_SERVICE_API_KEY` - API key for external service

**Optional Secrets:**
- `YOUR_SERVICE_CONFIG` - Extended configuration

---

## NATS Integration

### Subjects Published

| Subject | Description |
|----------|-------------|
| `your-service.processed.v1` | Widget processing completed |
| `your-service.error.v1` | Processing errors |

### Subjects Subscribed

| Subject | Description |
|----------|-------------|
| `ingest.widget.added.v1` | New widget to process |

### Service Discovery

Service announces itself on startup via `pmoves_announcer`:

```python
from pmoves_announcer import announce_service

await announce_service(
    slug="your-service-slug",
    name="Your Service Name",
    url="http://your-service-slug:8080",
    port=8080,
    tier="api"
)
```

---

## Service Discovery

### Services Used

| Service | Slug | Purpose |
|---------|------|---------|
| TensorZero | `tensorzero` | LLM calls for widget analysis |
| NATS | `nats` | Message bus for coordination |

### Discovery Pattern

```python
from pmoves_registry import get_service_url

tensorzero_url = await get_service_url("tensorzero", default_port=3030)
```

---

## Health Monitoring

### Health Check Implementation

Uses `pmoves_health` for standard health endpoint:

```python
from pmoves_health import HealthChecker, DatabaseCheck, NATSCheck

checker = HealthChecker("your-service-slug")
checker.database(check_db_connection)
checker.nats(os.getenv("NATS_URL"))
```

### Health Endpoint

`GET /healthz`

**Response:**
```json
{
  "status": "healthy",
  "service": "your-service-slug",
  "database_connected": true,
  "nats_connected": true
}
```

---

## Docker Integration

### Image

```dockerfile
FROM ghcr.io/POWERFULMOVES/your-service-slug:latest
```

### Docker Compose

```yaml
services:
  your-service-slug:
    image: ghcr.io/POWERFULMOVES/your-service-slug:latest
    ports:
      - "8080:8080"
    environment:
      - NATS_URL=${NATS_URL}
      - TENSORZERO_URL=${TENSORZERO_URL}
      - YOUR_SERVICE_API_KEY=${YOUR_SERVICE_API_KEY}
    networks:
      - pmoves_app
```

---

## Deployment

### Standalone Mode

```bash
docker compose -f docker-compose.standalone.yml up -d
```

**Differences:**
- Uses local Ollama for LLM (if applicable)
- No NATS connection
- Local databases only

### Docked Mode (PMOVES.AI)

```bash
docker compose -f docker-compose.yml up -d
```

**Additional capabilities:**
- Publishes events to NATS
- Uses TensorZero for LLM
- Discovers other services via registry
- Exposes metrics to Prometheus

---

## Development

### Local Development

```bash
# Install dependencies
uv sync

# Run locally
uv run python -m your_service.main

# Run with Docker
docker compose up --build
```

### Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov
```

---

## Integration Checklist

- [ ] Copy integration packages: `pmoves_announcer/`, `pmoves_registry/`, `pmoves_health/`, `pmoves_common/`
- [ ] Create `chit/secrets_manifest_v2.yaml`
- [ ] Implement `/healthz` endpoint
- [ ] Announce service on startup via NATS
- [ ] Subscribe to relevant NATS subjects
- [ ] Add environment variables to `env.shared`
- [ ] Add service to parent `docker-compose.pmoves.yml`
- [ ] Test service discovery
- [ ] Test health monitoring
- [ ] Update documentation

---

## Troubleshooting

### Service Not Discoverable

1. Check NATS connection
2. Verify service announcement on `services.announce.v1`
3. Check `/healthz` endpoint returns 200

### Environment Variables Not Loading

1. Verify `env.shared` includes service variables
2. Check `CHIT_ENVIRONMENT` is set correctly
3. Run bootstrap script: `scripts/bootstrap_credentials.sh`

---

## References

- [PMOVES.AI Integration Guide](../pmoves/docs/PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md)
- [NATS Service Discovery](../pmoves/docs/NATS_SERVICE_DISCOVERY.md)
- [Health Check Patterns](../pmoves/docs/PMOVES_HEALTH_PATTERNS.md)
- [CHIT v2 Specification](../pmoves/docs/CHIT_V2_SPECIFICATION.md)

---

**Maintainer:** Your Name
**Contact:** @your-username
