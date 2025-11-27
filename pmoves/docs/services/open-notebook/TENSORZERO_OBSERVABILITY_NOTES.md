# TensorZero Gateway Observability (ClickHouse)

The 2025.10.7 gateway release moved ClickHouse settings under `gateway.observability.clickhouse`. The legacy `[clickhouse]` table no longer parses and results in `clickhouse: unknown field` during boot.

## Current status (local bundles)
- Observability is **disabled by default** so the gateway can start without ClickHouse credentials. ClickHouse still runs alongside the gateway profile (`make -C pmoves up-tensorzero`) so metrics can be enabled later.
- Enable observability only after the `gateway.observability.clickhouse` block is present in `pmoves/tensorzero/config/tensorzero.toml` and credentials are supplied.

## Enabling metrics
1. Copy the example block below into `pmoves/tensorzero/config/tensorzero.toml` (or uncomment it if already present).
2. Populate the secrets in your environment (recommended):
   - `TENSORZERO_OBS_CLICKHOUSE_URL` (e.g., `http://tensorzero-clickhouse:8123`)
   - `TENSORZERO_OBS_CLICKHOUSE_DATABASE` (default `default`)
   - `TENSORZERO_OBS_CLICKHOUSE_USERNAME` (default `default`)
   - `TENSORZERO_OBS_CLICKHOUSE_PASSWORD`
3. Flip `observability.enabled` to `true` and restart: `make -C pmoves up-tensorzero`.

```toml
[gateway]
observability.enabled = true

[gateway.observability.clickhouse]
url = "env::TENSORZERO_OBS_CLICKHOUSE_URL"
database = "env::TENSORZERO_OBS_CLICKHOUSE_DATABASE"
username = "env::TENSORZERO_OBS_CLICKHOUSE_USERNAME"
password = "env::TENSORZERO_OBS_CLICKHOUSE_PASSWORD"
```

If you prefer hard-coded values for local-only testing, replace the `env::` entries with static strings (e.g., `url = "http://tensorzero-clickhouse:8123"`, `database = "default"`).

## Verification steps
- Run `curl http://127.0.0.1:8123/ping` to confirm ClickHouse is reachable.
- Start the gateway and check for `observability exporter configured` in the logs; errors about unknown fields should disappear once the new table is present.
- Query recent points to confirm ingestion (example for traces table will vary with the upstream schema). Until we finalize the table names, expect write errors if the block is omitted or credentials are missing.
