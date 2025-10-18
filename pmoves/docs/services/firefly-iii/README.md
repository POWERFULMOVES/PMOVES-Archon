# firefly-iii — Integration Guide

Status: In progress (external stack; compose bundle available)

Overview
- Firefly III is a self-hosted personal finance manager with a REST API and personal access tokens.
- In PMOVES, treat Firefly as a finance telemetry source for budgeting insights, spend summaries, and goal tracking.

Deployment
- Reference bundle: `pmoves/docs/PMOVES.AI PLANS/WGER - Firefly iii compose -integrations/`
- Quick start (with Wger + Firefly):
```
make -C "pmoves/docs/PMOVES.AI PLANS/WGER - Firefly iii compose -integrations" up
```

Networking/Ports
- Default Firefly web: `8080` (as defined in the compose bundle)

Environment
- `FIREFLY_BASE_URL` (e.g., `http://firefly:8080` on the compose network)
- `FIREFLY_ACCESS_TOKEN` (personal access token)

API/Contracts
- Endpoints of interest: `/api/v1/transactions`, `/api/v1/accounts`, `/api/v1/budgets`.
- Auth via `Authorization: Bearer <token>` header.

Runbook
- Store `FIREFLY_ACCESS_TOKEN` in PMOVES secrets.
- n8n flow polls Firefly transactions, normalizes categories, writes to Supabase.

Smoke
```
curl -sS -H "Authorization: Bearer $FIREFLY_ACCESS_TOKEN" "$FIREFLY_BASE_URL/api/v1/transactions?limit=1" | jq '.data[0] | {journal_id: .id, description: .attributes.description}'
```

Integration Review (PMOVES)
- Storage: `finance.transactions`, `finance.accounts`, `finance.budgets` in Supabase.
- Events: `finance.transactions.ingested.v1` emitted on new data to trigger analytics.
- Agents: Budget coach persona or dashboard generator consuming normalized tables.

Related Plans/Docs
- Compose bundle and scripts: `PMOVES.AI PLANS/WGER - Firefly iii compose -integrations/`

Next Steps
- Define Supabase schemas + RLS for finance domains.
- Add reconciliation job to dedupe/merge recurring transactions.

