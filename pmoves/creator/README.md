# PMOVES Creator Bundle

All ComfyUI-centric assets for WAN Animate, Qwen Image Edit+, and VibeVoice now live under `pmoves/creator/`. This bundle keeps the one-click installers, tutorial walkthroughs, and ready-to-import workflows that feed the creative n8n automations (`wan_to_cgp`, `qwen_to_cgp`, `vibevoice_to_cgp`).

## Directory Map

| Path | Contents | Notes |
| --- | --- | --- |
| `installers/` | One-click Windows/RunPod installers (`*.bat`, `*.sh`) for ComfyUI portable bundles, RVC helpers, FFmpeg, and supporting scripts. | Run from the render workstation; they lay down the portable ComfyUI stacks referenced in the tutorials. |
| `tutorials/` | Markdown guides (`*_tutorial.md`, `waninstall guide.md`, operator notes) plus supplemental write-ups (`imageedit.md`, `mumpitz*.md`). | Follow these before wiring the n8n webhooks; they define expected directories, prompts, and environment overrides. |
| `workflows/` | ComfyUI workflow exports (`*.json`) for WAN/Qwen/VibeVoice plus curated ADV Patreon graphs. | Import via ComfyUI Manager (Windows) or drop into `ComfyUI/input/graphs/` when using the portable builds. |
| `resources/ADV_Patreon/` | Additional ZIP-ready content (datasets, WAN LoRAs, workflow variants) referenced in the tutorials. | Keep this synced if you rely on Patreon-only graph updates. |

## Installing the Toolchains

Run the installers from `installers/` on the creative host. The table below mirrors the previous VibeVoice notes with updated paths.

| Installer | Purpose | n8n / Pipeline Signals |
| --- | --- | --- |
| `installers/VIBEVOICE-WEBUI_INSTALLER.bat` | Clones & launches the VibeVoice TTS WebUI; exposes webhook endpoints for audio renders. | Emits `voice_job_id` + storage paths used by the audio ingest flows. |
| `installers/VIBEVOICE-RVC-COMFYUI-MANAGER_AUTO_INSTALL.bat` | Installs ComfyUI portable with the VibeVoice node pack. Pair with `workflows/VIBEVOICE-RVC_VOICE_CLONING.json`. | Sends completion payloads (speaker metadata, storage URIs) to Supabase via the VibeVoice webhook. |
| `installers/VIBEVOICE-RVC-NODES_INSTALL.bat`, `installers/RVC_INSTALLER.bat` | Adds core RVC models/scripts consumed by the ComfyUI manager bundle. | Produces intermediate WAVs that n8n normalizes and publishes. |
| `installers/FFMPEG-INSTALL AS ADMIN.bat` | Installs FFmpeg system-wide on Windows render nodes. | Required when n8n invokes FFmpeg via `N8N_FFMPEG_PATH` to normalize audio. |
| `installers/QWEN-IMAGE-EDIT-*.{bat,sh}` | One-click installers for Qwen Image Edit+ (Windows + RunPod). | Prepares the ComfyUI environment expected by the Qwen webhook (`qwen_to_cgp`). |
| `installers/WAN-ANIMATE-*.{bat,sh}` | WAN Animate installers (portable ComfyUI, RunPod automation, models/nodes). | Aligns with `wan_to_cgp` payload structure; keep LoRAs in `resources/ADV_Patreon/wan2-1-loras`. |
| `installers/install_triton_and_sageattention_auto.bat` | Optional Triton/SageAttention acceleration helper used by multiple workflows. | Run after the base installer if you need faster inference on NVIDIA GPUs. |

### Environment Expectations (VibeVoice example)

- `SUPABASE_STORAGE_AUDIO_BUCKET` — Bucket where VibeVoice uploads audio renders.
- `VIBEVOICE_STORAGE_SERVICE_ROLE_KEY` — Supabase service-role key used by n8n to fetch protected files.
- `DISCORD_VOICE_WEBHOOK_URL` / `DISCORD_VOICE_WEBHOOK_USERNAME` — Webhook for preview clips.
- `N8N_FFMPEG_PATH` — Only needed if FFmpeg is not on `$PATH` inside the n8n container.

Configure these via `docker-compose.n8n.yml` or the n8n UI → Settings → Variables before activating the creative flows.

## Tutorials

Key walkthroughs live under `tutorials/`:

- `wan_animate_2.2_tutorial.md` — full WAN Animate install + workflow walkthrough.
- `qwen_image_edit_plus_tutorial.md` — ComfyUI + Qwen Image Edit+ setup and prompts.
- `vibevoice_tts_tutorial.md` — VibeVoice + RVC voice cloning pipeline.
- `waninstall guide.md`, `imageedit.md`, `mumpitz*.md` — supplemental notes, persona examples, installer tips.
- `vibevoice_operator_notes.md` — original operator-focused checklist for VibeVoice/RVC (migrated from the legacy README).

## Workflows

Import the `.json` workflows from `workflows/` using ComfyUI Manager or by dropping them into your `ComfyUI/input/graphs/` folder. The filenames track release dates and variants (e.g., `251007_MICKMUMPITZ_WAN-2-2-VID_ADV.json`). Keep them in sync with the tutorials and update MinIO bucket mappings in the nodes before running.

## Keeping Tutorials in Sync

When you update or add installers/tutorials:

1. Drop new assets into the appropriate subfolder.
2. Update this README with a short description and expected signals.
3. Review downstream documentation (Creator pipeline runbooks, smoke tests, service guides) so they reference `pmoves/creator/...`.

This keeps the creative toolchain discoverable for operators rolling out the n8n automations and Geometry Bus demos.
