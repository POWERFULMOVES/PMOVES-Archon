Verify health status of all PMOVES production services.

This command checks the `/healthz` endpoints for all deployed services to ensure the system is operational.

## Usage

Run this command when:
- Starting development to verify infrastructure is running
- Debugging issues to identify failing services
- Before deploying changes to validate system health
- After bringing up services with docker compose

## Implementation

Uses dynamic service discovery instead of hardcoded ports.

1. **Check if service discovery tool exists:**
   ```bash
   # Check if jq is available for JSON parsing
   if ! command -v jq >/dev/null 2>&1; then
       echo "⚠️  jq required for service discovery. Install: apt install jq / brew install jq"
       FALLBACK=1
   else
       FALLBACK=0
   fi

   if [ "$FALLBACK" -eq 1 ]; then
       # Legacy fallback with hardcoded ports
       echo "Using legacy port-based health checks..."
       echo ""
       echo "**Agent Coordination**"
       curl -sf http://localhost:8080/healthz && echo "  ✓ Agent Zero" || echo "  ✗ Agent Zero"
       curl -sf http://localhost:8091/healthz && echo "  ✓ Archon" || echo "  ✗ Archon"
       curl -sf http://localhost:8097/healthz && echo "  ✓ Channel Monitor" || echo "  ✗ Channel Monitor"
       echo ""
       echo "**Retrieval & Knowledge**"
       curl -sf http://localhost:8086/healthz && echo "  ✓ Hi-RAG v2 CPU" || echo "  ✗ Hi-RAG v2 CPU"
       curl -sf http://localhost:8087/healthz && echo "  ✓ Hi-RAG v2 GPU" || echo "  ✗ Hi-RAG v2 GPU"
       curl -sf http://localhost:8099/healthz && echo "  ✓ SupaSerch" || echo "  ✗ SupaSerch"
       curl -sf http://localhost:8098/healthz && echo "  ✓ DeepResearch" || echo "  ✗ DeepResearch"
       echo ""
       echo "**Media Processing**"
       curl -sf http://localhost:8077/healthz && echo "  ✓ PMOVES.YT" || echo "  ✗ PMOVES.YT"
       curl -sf http://localhost:8078/healthz && echo "  ✓ FFmpeg-Whisper" || echo "  ✗ FFmpeg-Whisper"
       curl -sf http://localhost:8079/healthz && echo "  ✓ Media-Video Analyzer" || echo "  ✗ Media-Video Analyzer"
       curl -sf http://localhost:8082/healthz && echo "  ✓ Media-Audio Analyzer" || echo "  ✗ Media-Audio Analyzer"
       curl -sf http://localhost:8083/healthz && echo "  ✓ Extract Worker" || echo "  ✗ Extract Worker"
       curl -sf http://localhost:8084/healthz && echo "  ✓ LangExtract" || echo "  ✗ LangExtract"
       curl -sf http://localhost:8092/healthz && echo "  ✓ PDF Ingest" || echo "  ✗ PDF Ingest"
       curl -sf http://localhost:8095/healthz && echo "  ✓ Notebook Sync" || echo "  ✗ Notebook Sync"
       echo ""
       echo "**Utilities**"
       curl -sf http://localhost:8088/healthz && echo "  ✓ Presign" || echo "  ✗ Presign"
       curl -sf http://localhost:8085/healthz && echo "  ✓ Render Webhook" || echo "  ✗ Render Webhook"
       curl -sf http://localhost:8093/healthz && echo "  ✓ Jellyfin Bridge" || echo "  ✗ Jellyfin Bridge"
       curl -sf http://localhost:8094/healthz && echo "  ✓ Publisher-Discord" || echo "  ✗ Publisher-Discord"
   else
       # Use service discovery for dynamic port detection
       echo "Using dynamic service discovery..."
       /pmoves:services --json | jq -r '
           .services | to_entries[] | select(.value != null) |
           "\n\(.key): \(.value.name) - Port: \(.value.ports[0] // "unknown") - Status: "
               + (if .value.health == "running" then "✓" else "✗") +
               (if .value.ports[0] then " (\(.value.ports[0]))" else "")
       '
   fi
   ```bash
   # Agent Coordination
   curl -f http://localhost:8080/healthz  # Agent Zero
   curl -f http://localhost:8091/healthz  # Archon
   curl -f http://localhost:8097/healthz  # Channel Monitor

   # Retrieval & Knowledge
   curl -f http://localhost:8086/healthz  # Hi-RAG v2 CPU
   curl -f http://localhost:8087/healthz  # Hi-RAG v2 GPU
   curl -f http://localhost:8099/healthz  # SupaSerch
   curl -f http://localhost:8098/healthz  # DeepResearch

   # Media Processing
   curl -f http://localhost:8077/healthz  # PMOVES.YT
   curl -f http://localhost:8078/healthz  # FFmpeg-Whisper
   curl -f http://localhost:8079/healthz  # Media-Video Analyzer
   curl -f http://localhost:8082/healthz  # Media-Audio Analyzer
   curl -f http://localhost:8083/healthz  # Extract Worker
   curl -f http://localhost:8084/healthz  # LangExtract
   curl -f http://localhost:8092/healthz  # PDF Ingest
   curl -f http://localhost:8095/healthz  # Notebook Sync

   # Utilities
   curl -f http://localhost:8088/healthz  # Presign
   curl -f http://localhost:8085/healthz  # Render Webhook
   curl -f http://localhost:8093/healthz  # Jellyfin Bridge
   curl -f http://localhost:8094/healthz  # Publisher-Discord
   ```

3. **Report results:**
   - List all healthy services (✓)
   - Highlight any failing services (✗) with service name and port
   - Suggest remediation (check logs, restart service)

## Notes

- Health endpoints check service status + dependency connectivity (NATS, Supabase, etc.)
- Use `-f` flag with curl to fail on non-200 responses
- If services are down, check docker compose: `docker compose ps`
- View logs: `docker compose logs <service-name>`
- Most services are in specific compose profiles (agents, workers, orchestration, etc.)
