# PMOVES Health Check Patterns

**Purpose:** Document standard health check patterns for PMOVES.AI services.

**Last Updated:** 2026-02-12

---

## Overview

All PMOVES.AI services should expose a `/healthz` endpoint following these conventions:

**Response Format:**
```json
{
  "status": "healthy",
  "service": "my-service",
  "timestamp": "2026-02-12T10:00:00Z",
  "database_connected": true,
  "nats_connected": true,
  "checks": {
    "memory_ok": true
  }
}
```

**Status Values:**
- `healthy` - All checks passing
- `degraded` - Optional checks failing, service still functional
- `unhealthy` - Required checks failing, service may not work correctly

---

## pmoves_health Package

**Location:** `pmoves_health/` directory in each service

**Purpose:** Standard health check implementation with dependency checks

### Key Classes

| Class | Purpose |
|--------|---------|
| `HealthChecker` | Main health checker with multiple dependency checks |
| `DependencyCheck` | Base class for dependency health checks |
| `DatabaseCheck` | Database connection health check |
| `HTTPCheck` | HTTP endpoint health check |
| `NATSCheck` | NATS connection health check |
| `HealthStatus` | Health status constants enum |

### Usage Examples

**Basic Health Endpoint:**
```python
from pmoves_health import create_health_app

# Create minimal FastAPI app with health check
app = create_health_app(service_name="My Service")
```

**Add to Existing FastAPI:**
```python
from fastapi import FastAPI
from pmoves_health import health_check_router

app = FastAPI()
app.include_router(health_check_router)
```

**With Custom Checks:**
```python
from pmoves_health import HealthChecker, DatabaseCheck, HTTPCheck

checker = HealthChecker("my-service")

# Add dependency checks
checker.database(lambda: connect_to_database())
checker.http("http://other-service:8080/healthz", name="other-service")

# Add custom check
async def check_memory():
    import psutil
    return psutil.virtual_memory().percent < 90

checker.add_custom_check("memory_ok", check_memory)

# Get health status
status = await checker.check_all()
```

**Decorator Pattern:**
```python
from pmoves_health import health_check, DatabaseCheck, HTTPCheck

@health_check([
    DatabaseCheck(lambda: db.connect()),
    HTTPCheck("http://api:8080/healthz", name="api")
])
async def my_handler():
    return {"message": "OK"}
```

---

## Health Check Patterns

### Database Health Check

**PostgreSQL/Supabase:**
```python
import asyncpg
from pmoves_health import HealthChecker

checker = HealthChecker("my-service")

async def check_db():
    try:
        conn = await asyncpg.connect("postgres://...")
        await conn.close()
        return True
    except Exception:
        return False

checker.database(check_db)
```

**SurrealDB:**
```python
from surrealdb import AsyncSurreal
from pmoves_health import HealthChecker

checker = HealthChecker("my-service")

async def check_db():
    try:
        async with AsyncSurreal("...") as db:
            await db.query("SELECT * FROM $session")
        return True
    except Exception:
        return False

checker.database(check_db)
```

### HTTP Service Health Check

```python
from pmoves_health import HealthChecker

checker = HealthChecker("my-service")

# Add HTTP check
checker.http("http://other-service:8080/healthz", name="other-service")
```

### NATS Health Check

```python
import os
from pmoves_health import HealthChecker

checker = HealthChecker("my-service")

nats_url = os.getenv("NATS_URL", "nats://nats:4222")
checker.nats(nats_url)
```

### Custom Health Checks

**Memory Check:**
```python
import psutil
from pmoves_health import HealthChecker

checker = HealthChecker("my-service")

async def memory_check():
    return psutil.virtual_memory().percent < 90

checker.add_custom_check("memory_ok", memory_check)
```

**Disk Space Check:**
```python
import shutil
from pmoves_health import HealthChecker

checker = HealthChecker("my-service")

async def disk_check():
    return shutil.disk_usage("/").percent < 90

checker.add_custom_check("disk_ok", disk_check)
```

**Service-Specific Check:**
```python
from pmoves_health import HealthChecker

checker = HealthChecker("my-service")

async def check_llm_provider():
    # Check if LLM provider is accessible
    response = await llm_client.generate("test")
    return response.status == "success"

checker.add_custom_check("llm_provider_ok", check_llm_provider)
```

---

## Required vs Optional Checks

**Required Checks** (service unhealthy if failing):
- Database connection (if service uses database)
- NATS connection (if service publishes/subscribes to NATS)
- Critical external services

**Optional Checks** (service degraded if failing):
- Non-critical external services
- Memory/disk thresholds
- Custom business logic checks

```python
from pmoves_health import DatabaseCheck, HTTPCheck

# Required: database (default required=True)
DatabaseCheck(connect_fn, required=True)

# Optional: external service
HTTPCheck(url, name="service", required=False)
```

---

## Integrating with Service Startup

### FastAPI Lifespan

```python
from fastapi import FastAPI
from pmoves_health import HealthChecker, add_nats_check
import os

app = FastAPI()

# Global health checker
health_checker = HealthChecker("my-service")

@app.on_event("startup")
async def startup():
    # Configure health checks
    nats_url = os.getenv("NATS_URL", "nats://nats:4222")
    add_nats_check(nats_url)

@app.get("/healthz")
async def health_check():
    return await health_checker.check_all()
```

### With Background Health Monitoring

```python
import asyncio
from pmoves_health import HealthChecker

async def health_monitor_loop(checker: HealthChecker, interval: int = 30):
    """Run health checks periodically and log results."""
    while True:
        status = await checker.check_all()
        if status["status"] != "healthy":
            print(f"Health check failed: {status}")
        await asyncio.sleep(interval)

# Start background monitor
asyncio.create_task(health_monitor_loop(health_checker))
```

---

## Prometheus Metrics Integration

Health status can be exposed as Prometheus metrics:

```python
from prometheus_client import Counter, Gauge

# Metrics
health_check_total = Counter('health_check_total', 'Total health checks', ['service', 'status'])
health_status = Gauge('health_status', 'Current health status', ['service'])

async def health_with_metrics():
    status = await health_checker.check_all()

    # Update metrics
    health_check_total.labels(
        service="my-service",
        status=status["status"]
    ).inc()
    health_status.labels(
        service="my-service"
    ).set(1 if status["status"] == "healthy" else 0)

    return status
```

---

## Troubleshooting

### Health Check Timeout

If dependency checks are timing out:

```python
from pmoves_health import HTTPCheck

# Increase timeout (default 2s for HTTPCheck)
# For custom timeout, implement custom check:
async def check_with_timeout():
    try:
        async with asyncio.timeout(10.0):
            # Your check logic here
            pass
    except asyncio.TimeoutError:
        return False
```

### Circular Dependencies

If Service A depends on Service B and Service B depends on Service A:

```python
# Service A: Check only database, not Service B
checker = HealthChecker("service-a")
checker.database(check_db)

# Service B: Check database and NATS, not Service A
checker = HealthChecker("service-b")
checker.database(check_db)
checker.nats(nats_url)
```

### Degraded State

When to return `degraded`:
- Service is functional but with reduced capacity
- Optional services are unavailable
- Performance is below normal thresholds
- Non-critical external dependencies are down

---

## Testing Health Checks

### Unit Test

```python
import pytest
from pmoves_health import HealthChecker

@pytest.mark.asyncio
async def test_health_checker():
    checker = HealthChecker("test-service")

    # Add mock check
    async def mock_check():
        return True

    checker.add_custom_check("mock", mock_check)

    status = await checker.check_all()
    assert status["status"] == "healthy"
```

### Integration Test

```bash
# Test health endpoint
curl http://localhost:8080/healthz

# Expected response
{
  "status": "healthy",
  "service": "my-service",
  "timestamp": "2026-02-12T10:00:00Z"
}
```

---

## Related Documentation

- [NATS_SERVICE_DISCOVERY.md](NATS_SERVICE_DISCOVERY.md) - Service discovery via NATS
- [PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md](PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md) - Integration guide
- [SERVICE_HEALTH_ENDPOINTS.md](SERVICE_HEALTH_ENDPOINTS.md) - Service health endpoint catalog

---

**Maintainer:** PMOVES.AI Team
