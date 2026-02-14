# Archon PMOVES Integration Overlay

This overlay defines the PMOVES integration contract for Archon when consumed as a submodule.

## Hook surface

- Event hook: pmoves-announcer subjects declared in events/subjects.yaml.
- Model hook: tensorzero-gateway and model-registry mappings via models/mappings.
- GPU hook: gpu-orchestrator compatibility through mesh.gpu.model.loaded.v1 and mesh.gpu.model.unloaded.v1.
- Validation can-openers: tools/validate-submodule.sh, tools/submodule-sitrep.sh, tools/validate-integration.sh.

## Notes

- Runtime compose changes should stay in root PMOVES compose files; compose/docker-compose.pmoves-net.yml is an overlay extension point.
- This folder is intended for PMOVES contract compatibility and onboarding automation.
