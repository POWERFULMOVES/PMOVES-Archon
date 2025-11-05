# Venice + TensorZero Integration (PMOVES)

1) Copy `tensorzero.toml` and `.env.tensorzero.example` to your repo root.
   - Rename `.env.tensorzero.example` -> `.env.tensorzero` and put real values.

2) Merge `compose.overrides.tensorzero.yml` and `compose.overrides.agents.yml` into your Docker Compose (or pass with `-f`).

3) Ensure Agent Zero and Hi-RAG services pick up the new env_files:
   - `.env.agent-zero.override` (written by models_sync.py)
   - `.env.hirag.override`      (written by models_sync.py)

4) Bring up:
   docker compose -f docker-compose.yml -f compose.overrides.tensorzero.yml -f compose.overrides.agents.yml up -d

5) Point all OpenAI-compatible clients to TensorZero:
   OPENAI_COMPAT_BASE_URL=http://tensorzero:3000

6) Set Venice key in `.env.tensorzero`:
   VENICE_API_KEY=...

7) (Optional) Expose TensorZero via Cloudflare Tunnel for remote Jetsons/VPS.
