# Operations - archon

## Checks

- ../tools/validate-submodule.sh
- ../tools/submodule-sitrep.sh
- ../tools/validate-integration.sh .. --strict-hooks

## Bring-up

1. Configure secrets via CHIT + secrets funnel.
2. Start Archon stack from the PMOVES root compose workflow.
3. Apply any Archon-specific n8n flow changes under n8n/flows.

## Auth/bootstrap order

1. Run PMOVES auth bootstrap (make -C pmoves auth-bootstrap).
2. Run this overlay bootstrap if needed (../auth/bootstrap.sh).

## Smoke checks

- make -C pmoves auth-check
- make -C pmoves monitoring-status

## Rollback

1. Revert overlay file changes.
2. Re-run validation checks.
3. Restart relevant services.
