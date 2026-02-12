# NATS Service Discovery in PMOVES.AI

**Purpose:** Document how PMOVES.AI services discover each other using NATS message bus and the pmoves_announcer/pmoves_registry integration packages.

**Last Updated:** 2026-02-12

---

## Overview

PMOVES.AI uses a **publish-subscribe pattern** for service discovery via NATS:

```
┌─────────────────────────────────────────────────────────────┐
│                    NATS Message Bus (port 4222)          │
│                    nats://nats:4222                      │
├─────────────────────────────────────────────────────────────┤
│                 Service Discovery Layer                      │
│     ┌─────────────────────────────────────────────────┐   │
│     │  pmoves_announcer (package)              │   │
│     │  - announce_service() - Register service     │   │
│     │  - ServiceAnnouncer - Full API            │   │
│     │  - BackgroundAnnouncer - Periodic re-announce │   │
│     └─────────────────────────────────────────────────┘   │
│                                                         │
│     ┌─────────────────────────────────────────────────┐   │
│     │  pmoves_registry (package)              │   │
│     │  - get_service_url() - Resolve service     │   │
│     │  - get_service_info() - Full metadata      │   │
│     │  - check_service_health() - Health check     │   │
│     └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

                    ▼
┌─────────────────────────────────────────────────────────┐
│              Services can discover each other      │
│        - Query pmoves_registry for URLs          │
│        - Subscribe to NATS subjects             │
│        - Call service health endpoints            │
└───────────────────────────────────────────────────────┘
```

---

## NATS Subject: services.announce.v1

**Subject:** `services.announce.v1`

**Message Format (JSON):**
```json
{
  "slug": "hirag-v2",
  "name": "Hi-RAG Gateway v2",
  "url": "http://hi-rag-gateway-v2:8086",
  "health_check": "http://hi-rag-gateway-v2:8086/healthz",
  "tier": "api",
  "port": 8086,
  "timestamp": "2026-02-12T10:00:00Z",
  "metadata": {
    "gpu_port": 8087,
    "features": ["vector", "graph", "fulltext"],
    "rerank_enabled": true
  }
}
```

---

## Integration Packages

### pmoves_announcer

**Location:** Each service has `pmoves_announcer/` directory with `__init__.py`

**Purpose:** Publish service availability announcements to NATS

**Key Classes:**

| Class | Purpose |
|--------|---------|
| `ServiceAnnouncement` | Data class for announcement message format |
| `ServiceAnnouncer` | Main announcer with announce() method |
| `BackgroundAnnouncer` | Periodic re-announcement (e.g., every 60s) |
| `ServiceTier` (Enum) | Service tier classification |

**Usage Example:**
```python
from pmoves_announcer import announce_service, ServiceTier

# Simple announcement
await announce_service(
    slug="hirag-v2",
    name="Hi-RAG Gateway v2",
    url="http://hi-rag-gateway-v2:8086",
    port=8086,
    tier=ServiceTier.API,
    metadata={"gpu_port": 8087}
)
```

**With Custom Health Check:**
```python
from pmoves_announcer import ServiceAnnouncer

announcer = ServiceAnnouncer(
    slug="my-service",
    name="My Service",
    url="http://my-service:8080",
    port=8080,
    tier="worker",
    health_check="http://my-service:8080/custom/health",  # Custom
    nats_url="nats://custom-nats:4222",  # Custom NATS
    metadata={"version": "1.0.0"}
)

await announcer.announce()
```

**Background Announcer:**
```python
from pmoves_announcer import ServiceAnnouncer, BackgroundAnnouncer

announcer = ServiceAnnouncer(
    slug="bg-service",
    name="Background Service",
    url="http://bg-service:8081",
    port=8081,
    tier="worker"
)

bg = BackgroundAnnouncer(announcer, interval=60)  # Re-announce every 60s
await bg.start()
```

---

### pmoves_registry

**Location:** Each service has `pmoves_registry/` directory with `__init__.py`

**Purpose:** Discover other services using environment-based URL resolution with fallback chain

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `get_service_url(slug)` | Resolve service URL with fallback chain |
| `get_service_info(slug)` | Get full ServiceInfo with metadata |
| `check_service_health(slug)` | Call health endpoint and return status |
| `CommonServices.get(name)` | Quick access to common service URLs |

**Fallback Chain (Priority Order):**
1. **Environment variable** - `<SLUG>_URL` (e.g., `HIRAG_V2_URL`)
2. **Constructed URL** - `http://<slug>:<default_port>`

**Usage Example:**
```python
from pmoves_registry import get_service_url, get_service_info, check_service_health

# Get service URL
hirag_url = await get_service_url("hirag-v2", default_port=8086)
# Returns: "http://hi-rag-gateway-v2:8086" (or from env var)

# Get full service info
info = await get_service_info("hirag-v2", default_port=8086)
print(f"{info.name}: {info.health_check_url}")

# Check health
healthy = await check_service_health("hirag-v2", default_port=8086)
```

**CommonServices Quick Access:**
```python
from pmoves_registry import CommonServices

agent_zero_url = CommonServices.get("agent_zero")  # http://agent-zero:8080
tensorzero_url = CommonServices.get("tensorzero")  # http://tensorzero-gateway:3030
hirag_v2_url = CommonServices.get("hirag_v2")  # http://hi-rag-gateway-v2:8086
```

---

## Service Tiers

PMOVES.AI uses a **6-tier architecture** for service classification:

| Tier | Description | Example Services |
|-------|-------------|------------------|
| `api` | Gateway and API services | Archon, HiRAG, Agent Zero |
| `llm` | LLM provider services | TensorZero |
| `media` | Media processing | Ultimate-TTS-Studio, Pipecat |
| `agent` | Agent services | Agent Zero, BoTZ |
| `worker` | Background workers | Extract Worker, LangExtract |
| `data` | Data storage services | Qdrant, Neo4j, Meilisearch |

---

## Environment Variable Configuration

Services can override discovered URLs via environment variables:

**Format:** `<SERVICE_SLUG>_URL`

**Examples:**
```bash
# Override Hi-RAG v2 URL
HIRAG_V2_URL=http://custom-hirag:8086

# Override Agent Zero URL
AGENT_ZERO_URL=http://custom-agent-zero:8080

# Environment variable patterns checked (in order):
# 1. HIRAG_V2_URL       (slug with underscores)
# 2. HIRAGV2_URL        (slug without hyphens)
# 3. HIRAG-V2_URL       (slug with hyphens - not recommended)
```

---

## Adding Service Discovery to a New Service

### Step 1: Copy Integration Packages

```bash
# In your new service directory
cd PMOVES-NewService

# Copy integration packages from PMOVES.AI template
cp -r /path/to/pmoves/templates/submodule/pmoves_announcer ./
cp -r /path/to/pmoves/templates/submodule/pmoves_registry ./
```

### Step 2: Announce on Startup

In your service's `main.py` or startup code:

```python
from pmoves_announcer import announce_service, BackgroundAnnouncer, ServiceAnnouncer
import asyncio

async def startup():
    # Simple announcement
    await announce_service(
        slug="my-new-service",
        name="My New Service",
        url=f"http://my-new-service:{os.getenv('PORT', '8080')}",
        port=int(os.getenv('PORT', 8080)),
        tier="api"
    )

    # Or use background announcer for periodic re-announcement
    announcer = ServiceAnnouncer(
        slug="my-new-service",
        name="My New Service",
        url=f"http://my-new-service:{os.getenv('PORT', '8080')}",
        port=int(os.getenv('PORT', 8080)),
        tier="api"
    )
    bg = BackgroundAnnouncer(announcer, interval=60)
    await bg.start()
```

### Step 3: Discover Other Services

```python
from pmoves_registry import get_service_url, check_service_health

async def call_other_service():
    # Discover Hi-RAG
    hirag_url = await get_service_url("hirag-v2", default_port=8086)

    # Check health first
    if await check_service_health("hirag-v2", default_port=8086):
        # Call the service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{hirag_url}/hirag/query",
                json={"query": "test query"}
            )
            return response.json()
```

---

## NATS Configuration

**Default NATS URL:** `nats://nats:4222`

**Environment Variable:** `NATS_URL`

**Connection Example:**
```python
from nats.aio.client import Client as NATS

nats_url = os.getenv("NATS_URL", "nats://nats:4222")
nc = await NATS.connect(nats_url)

# Subscribe to service announcements
sub = await nc.subscribe("services.announce.v1", cb=handle_announcement)

async def handle_announcement(msg):
    data = json.loads(msg.data.decode())
    print(f"Service announced: {data['name']}")
```

---

## Service Discovery Flow

### Service Startup

```
┌─────────────────────┐
│ Service Starts       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────┐
│ 1. Load configuration             │
│    - Read environment variables   │
│    - Set up NATS connection      │
└─────────┬─────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│ 2. Announce service               │
│    - Publish to services.announce.v1│
└─────────┬─────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│ 3. Listen for announcements        │
│    - Subscribe to NATS subjects   │
│    - Build local service cache     │
└───────────────────────────────────┘
```

### Service Discovery

```
┌─────────────────────────────────────────────┐
│ Service needs to call another service    │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│ 1. Check environment variables      │
│    - <SERVICE>_URL override         │
└─────────┬─────────────────────────┘
          │ (not found?)
          ▼
┌─────────────────────────────────────┐
│ 2. Use Docker DNS fallback         │
│    - http://service-slug:port     │
└─────────┬─────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│ 3. Verify health                   │
│    - Call /healthz endpoint        │
└─────────┬─────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│ 4. Make service call              │
└───────────────────────────────────┘
```

---

## Health Check Pattern

All PMOVES.AI services should expose a `/healthz` endpoint:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/healthz")
async def health_check():
    return {
        "status": "healthy",
        "service": "my-service",
        "version": "1.0.0"
    }
```

**Expected Response:** `200 OK` with JSON body

---

## Monitoring Service Discovery

### Check NATS Connection

```bash
# Using NATS CLI
nats server check nats://nats:4222

# Using docker exec
docker exec -it my-service nats server check nats://nats:4222
```

### Monitor Service Announcements

```bash
# Subscribe to announcements
nats sub "services.announce.v1"

# Or using docker exec
docker exec -it nats nats sub "services.announce.v1"
```

### Verify Service Discovery

```bash
# Check if service is discoverable
curl http://service-slug:port/healthz

# Check environment variable override
curl $SERVICE_SLUG_URL/healthz
```

---

## Troubleshooting

### Service Not Discoverable

1. **Check NATS connection:** Verify service can connect to NATS
2. **Check announcement:** Verify service publishes to `services.announce.v1`
3. **Check health endpoint:** Verify `/healthz` returns 200 OK
4. **Check environment variables:** Ensure correct `<SERVICE>_URL` format

### URL Resolution Failing

1. **Check slug format:** Use lowercase with hyphens (e.g., `hirag-v2`)
2. **Check default port:** Ensure service port is correct
3. **Check DNS:** Verify Docker DNS can resolve service name

### Background Announcer Not Working

1. **Check interval:** Ensure interval is reasonable (60s+ recommended)
2. **Check asyncio task:** Verify background task is running
3. **Check NATS reconnection:** Verify announcer handles connection loss

---

## Related Documentation

- [PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md](PMOVES.AI_SUBMODULE_INTEGRATION_GUIDE.md) - Full integration guide
- [SUBMODULE_LIST.md](SUBMODULE_LIST.md) - Complete submodule catalog
- [PORT_REGISTRY.md](PORT_REGISTRY.md) - Service port assignments
- [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) - Environment configuration

---

**Maintainer:** PMOVES.AI Team
