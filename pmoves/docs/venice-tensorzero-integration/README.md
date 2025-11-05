# Venice + TensorZero Integration

This guide shows how to use PMOVES with a local or remote TensorZero gateway and the bundled Ollama sidecar. It also covers switching providers for embeddings and wiring retrieval to preferred models.

## Quickstart
- Launch the stack: `make -C pmoves up-tensorzero`
  - Starts ClickHouse, TensorZero gateway (port 3030), TensorZero UI (port 4000), and Ollama sidecar (port 11434).
  - Visit http://localhost:4000 for the UI.

## Using remote inference
- Set `TENSORZERO_BASE_URL=http://<remote>:3000` to send embedding requests to a remote gateway.
- Optional: stop the local sidecar if not needed: `docker stop pmoves-pmoves-ollama-1`.

## hi-rag gateway settings
- TensorZero backend (default):
  - `EMBEDDING_BACKEND=tensorzero`
  - `TENSORZERO_BASE_URL=http://tensorzero-gateway:3000`
  - `TENSORZERO_EMBED_MODEL=tensorzero::embedding_model_name::gemma_embed_local`
- Ollama backend:
  - `USE_OLLAMA_EMBED=true`
  - `OLLAMA_URL=http://pmoves-ollama:11434`
  - `OLLAMA_EMBED_MODEL=embeddinggemma:300m`
- Fallback: if neither provider is reachable, hi-rag uses `SentenceTransformer` (`all-MiniLM-L6-v2`).

## Model selection tips
- Start with `embeddinggemma:300m` for speed; swap to larger variants as needed.
- For reranking, Qwen/Qwen3-Reranker-4B is pre-configured in the GPU gateway. The first run downloads the model (~2 minutes), later runs are fast.

## Troubleshooting
- If the UI shows “Route not found: POST /v1/embeddings”, ensure the gateway is on 3000 and `TENSORZERO_BASE_URL` matches.
- If Ollama cannot run on the host (e.g., Jetson), keep TensorZero remote and do not start the local sidecar; the gateway still works.
