# Creator Pipeline → CHIT & Personas (Field Guide)

This note ties the Creator pipeline to CHIT geometry and personas, so new assets and summaries flow into first‑class visualizations and grounded assistants.

## Pipeline Handshake
- Sources: YouTube (pmoves-yt), PDF ingest, Archon crawls, Open Notebook sync, Wger/Firefly (external), and the creative tutorial flows (WAN Animate, Qwen Image Edit+, VibeVoice) captured in PMOVES ART STUFF.
- Normalization: extract-worker → langextract (chunks), retrieval‑eval datasets, plus `tools/integrations/events_to_cgp.py` for creative envelopes emitted by n8n.
- Automation: n8n personas (`pmoves/n8n/flows/*`) orchestrate WAN/Qwen/VibeVoice render jobs, convert outputs into `content.publish.*` events, and forward health/finance summaries (`health.weekly.summary.v1`, `finance.monthly.summary.v1`).
- Geometry: CGP mappers turn summaries and creative metadata into `geometry.cgp.v1` packets (see `services/common/cgp_mappers.py`). Gateways warm caches, broadcast over Supabase Realtime, and optionally persist via `CHIT_PERSIST_DB=true`.

## CHIT Surfaces
- UI overlays: constellations blend wellness, finance, and creative assets so personas can jump from a finance trend to the latest WAN Animate render.
- Mind‑map: Neo4j alias graph provides anchors for personas; creative constellations inherit tags from n8n flows (`namespace`, `persona`, `prompt`).
- Avatars & Animation: the Geometry UI (`make -C pmoves web-geometry`) now exposes avatar cards that animate CHIT constellations using the WAN Animate outputs. Configure avatar metadata in Supabase (`persona_avatar` table) so the UI can autoplay geometry bus transitions.

## Personas
- Grounding packs: use retrieval‑eval outputs to ensure persona gates pass (MRR/NDCG thresholds) before n8n publishes persona-driven scripts.
- Evidence: archive mapper outputs and geometry screenshots in `docs/logs/` and persona evaluation tables; include WAN/Qwen/VibeVoice run IDs in `meta.geometry`.
- Interaction: personas reference CHIT constellations by ID to fetch jump locators, summaries, decoded labels, and avatars so PMOVES can render animated responses in UI chat.

## Creative Tutorials & Automation Hooks
- Tutorials: see the WAN Animate, Qwen Image Edit+, and VibeVoice guides under `PMOVES ART STUFF/`.
- Automation: n8n flows (`pmoves/n8n/flows/wan_to_cgp.json`, `qwen_to_cgp.json`, `vibevoice_to_cgp.json`) watch ComfyUI completions, call the creative scripts, and push geometry+Supabase updates automatically. Ensure `OPEN_NOTEBOOK_API_*`, `WGER_API_TOKEN`, and `FIREFLY_ACCESS_TOKEN` are set via `make bootstrap`.
- Personas-to-movie: combine `WAN Animate` + `VibeVoice` flows in n8n to storyboard, voice, and animate PMOVES avatars; the flows emit `content.publish.persona-film.v1` which the mappers translate into CGP clusters for avatar playback.

## How to Run Demos
- Start the stack: `make -C pmoves up` (GPU optional).
- Run creative automations: import/activate the n8n flows and trigger `wan_to_cgp` / `vibevoice_to_cgp` webhooks.
- Post health/finance CGPs: `make -C pmoves demo-health-cgp`, `make -C pmoves demo-finance-cgp`.
- Open the UI: `make -C pmoves web-geometry` and use avatar controls to animate CHIT constellations.
- Persist CGPs: set `CHIT_PERSIST_DB=true` and supply `PG*` env for hi‑rag‑gateway‑v2; query via PostgREST (see SMOKETESTS).

## References
- UI design: `docs/Unified and Modular PMOVES UI Design.md`
- CHIT decoder/spec: `pmoves/docs/PMOVESCHIT/PMOVESCHIT_DECODERv0.1.md`
- Creative tutorials: `pmoves/docs/PMOVES.AI PLANS/PMOVES ART STUFF/` (WAN Animate, Qwen Image Edit+, VibeVoice)
- n8n creative flows: `pmoves/n8n/flows/`
- Wger integration plan: `pmoves/docs/PMOVES.AI PLANS/WGER - Firefly iii compose -integrations/wger/Integration Plan_ PMOVES v5.12 and Wger Fitness Manager draft.md`
