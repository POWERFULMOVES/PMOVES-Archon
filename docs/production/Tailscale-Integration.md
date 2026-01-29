# Tailscale VPN Integration for PMOVES.AI

**Status:** Documented
**Last Updated:** 2026-01-29
**Purpose:** Production VPN access for remote management and multi-node deployment

---

## Overview

Tailscale provides secure, zero-config mesh VPN networking for PMOVES.AI production deployments. This enables:
- Remote access to services without exposing ports to the internet
- Secure multi-node communication across data centers
- ACL-based access control for team members
- Exit node functionality for secure outbound routing

## Installation

### On All Nodes

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale
tailscale up
```

### Authentication

```bash
# Using auth key (recommended for automated setup)
tailscale up --authkey=${TS_AUTH_KEY}

# Or interactive authentication
tailscale up
```

**Generate auth key:** https://login.tailscale.com/admin/settings/keys

## Configuration

### Exit Node (Remote Access)

For remote access to PMOVES services:

```bash
# Advertise this node as an exit node
tailscale up --advertise-exit-node
```

**ACL Configuration** (Tailscale Admin Console):
```json
{
  "tagOwners": {
    "tag:pmoves-service": ["autogroup:admin"],
    "tag:developer": ["autogroup:admin"]
  },
  "acls": [
    {"action": "accept", "src": ["tag:developer"], "dst": ["tag:pmoves-service:*"]},
    {"action": "accept", "src": ["tag:pmoves-service"], "dst": ["tag:pmoves-service:*"]}
  ],
  "ssh": [
    {"action": "accept", "src": ["tag:developer"], "dst": ["tag:pmoves-service"], "users": ["autogroup:nonroot"]}
  ]
}
```

### Subnet Router (Docker Network Access)

To expose PMOVES Docker networks to Tailscale:

```bash
# Advertise Docker network subnets
tailscale up --advertise-routes=172.30.0.0/16

# Verify routes advertised
tailscale status
```

**Routing table:**
| Subnet | Purpose | Services |
|--------|---------|----------|
| 172.30.1.0/24 | API Tier | TensorZero (3030), Agent Zero (8080) |
| 172.30.2.0/24 | App Tier | Hi-RAG (8086), Extract Worker (8083) |
| 172.30.3.0/24 | Bus Tier | NATS (4222) |
| 172.30.4.0/24 | Data Tier | Postgres (5432), Qdrant (6333) |
| 172.30.5.0/24 | Monitoring | Prometheus (9090), Grafana (3000) |

## Docker Compose Integration

### Tailscale Sidecar Service

```yaml
# docker-compose.tailscale.yml
services:
  tailscale:
    image: tailscale/tailscale:latest
    hostname: pmoves-${NODE_NAME}
    environment:
      - TS_AUTHKEY=${TS_AUTH_KEY}
      - TS_EXTRA_ARGS=--advertise-tags=tag:pmoves-service
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_USERSPACE=false
      - TS_PORT=41641
    volumes:
      - ts-data:/var/lib/tailscale
      - /dev/net/tun:/dev/net/tun
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    network_mode: host
    restart: unless-stopped

  # Example service accessible via Tailscale
  pmoves-service:
    network_mode: service:tailscale
    depends_on:
      - tailscale

volumes:
  ts-data:
```

### Environment Variables

```bash
# .env.tailscale
TS_AUTH_KEY=tskey-auth-xxxxx
TS_EXTRA_ARGS=--advertise-exit-node
TS_STATE_DIR=/var/lib/tailscale
```

## Usage

### Remote Access to Services

```bash
# Get Tailscale IP of a node
tailscale status

# Access services via Tailscale IP
curl http://100.x.x.x:3030/healthz  # TensorZero
curl http://100.x.x.x:8080/healthz  # Agent Zero
curl http://100.x.x.x:3000          # Grafana

# Or use hostname (if MagicDNS enabled)
curl http://pmoves-node-1.tailnet-name.ts.net:3030/healthz
```

### SSH Access

```bash
# SSH via Tailscale
ssh pmoves@pmoves-node-1

# Or with specific user
ssh root@pmoves-node-1
```

### Port Forwarding

```bash
# Forward local port to remote service
tailscale funnel 3030 localhost:3030

# Access via Tailscale IP
curl http://100.x.x.x:3030/healthz
```

## Security Best Practices

1. **ACL Enforcement:** Always use tags and ACLs to restrict access
2. **Key Rotation:** Rotate auth keys quarterly (90-day max age)
3. **Exit Node Control:** Only designate specific nodes as exit nodes
4. **Logging:** Enable Tailscale logging for audit trails
5. **Network Policies:** Combine with Docker network tier segmentation

## Troubleshooting

### Check Connection Status

```bash
tailscale status
tailscale ping pmoves-node-2
```

### View Logs

```bash
# Systemd logs
journalctl -u tailscaled -f

# Docker logs
docker logs tailscale
```

### Debug Routes

```bash
# Check advertised routes
tailscale status --json | jq '.TailscaleIPs'

# Test subnet router
ping -c 3 172.30.1.1  # API tier gateway
```

## Related Documentation

- [Network Tier Segmentation](../architecture/network-tier-segmentation.md)
- [PMOVES.AI-Edition-Hardened-Full](../PMOVES.AI-Edition-Hardened-Full.md)
- [Security Hardening Roadmap](../Security-Hardening-Roadmap.md)

## External References

- [Tailscale ACL Documentation](https://tailscale.com/kb/1018/acls/)
- [Tailscale Subnet Routers](https://tailscale.com/kb/1019/subnets/)
- [Tailscale Exit Nodes](https://tailscale.com/kb/1023/exit-nodes/)
- [Docker Integration Guide](https://tailscale.com/kb/1212/docker/)
