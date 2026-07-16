# Site Intelligence v2.13.0 — Connector Operations and Data Ingestion Control Center

## Purpose

v2.13.0 turns the existing connector collection into a managed operational layer. It does not replace source-specific adapters. It registers them, defines refresh jobs, records what happened during ingestion, and exposes controlled diagnostics for operators and public users.

## Managed scope

The registry contains 14 connector families:

- NASA POWER
- NASA GIBS
- Climate TRACE
- NOAA weather and climate
- EIA energy
- EPA AQS air quality
- Census context
- USGS land cover
- GBIF biodiversity
- World Bank
- OpenAlex
- Crossref
- GitHub
- Sustainable-development source registry

Each connector declares its provider, family, adapter, public status, expected update interval, quota policy, schema contract, transformations, datasets, and manual/scheduled/conditional job definition.

## Control-plane capabilities

- unified connector and dataset registry;
- manual, scheduled, and conditional refresh jobs;
- explicit due-job batch runner;
- execution receipts with timing, attempts, record counts, payload digest, source state, schema version, transformations, and validation results;
- source freshness and expected-update diagnostics;
- retry, exponential-backoff, quota-window, and circuit-breaker controls;
- payload-size and per-run record limits;
- schema validation and redacted quarantine records;
- accept, reject, and retry quarantine resolutions;
- public-safe status without credentials, quota internals, raw payloads, or private error detail; and
- file-backed zero-cost runtime paths that can be redirected through environment variables.

## Public endpoint

`GET /public/connectors/operations`

This endpoint exposes connector names, providers, families, public status, operational state, freshness state, last successful refresh, and public notes. It does not expose credential names, configured secrets, provider quota values, payload previews, or private execution errors.

## Administrative endpoints

The following routes are protected when `SC_SI_ADMIN_TOKEN` is configured:

- `GET /admin/connectors/control-center`
- `GET /admin/connectors/registry`
- `GET /admin/connectors/jobs`
- `GET /admin/connectors/jobs/due`
- `POST /admin/connectors/jobs/run-due`
- `POST /admin/connectors/jobs/{job_id}/run`
- `GET /admin/connectors/executions`
- `GET /admin/connectors/quarantine`
- `POST /admin/connectors/quarantine/{quarantine_id}/resolve`
- `GET /admin/connectors/datasets`

Job execution defaults to dry-run. Live retrieval must be explicitly requested.

## Explicit scheduler boundary

The backend evaluates whether jobs are due, but it does not claim that a persistent scheduler is running. Due jobs can be invoked through the protected batch endpoint or:

```bash
python scripts/run_connector_jobs_v2130.py --limit 10
```

The command is dry-run by default. Add `--live` only when live provider calls are intended.

## Runtime files

The following writable files are excluded from release manifests and Git:

- `backend/data/connector_operations_state_v2130.json`
- `backend/data/connector_operations_history_v2130.jsonl`
- `backend/data/connector_operations_quarantine_v2130.jsonl`

They can be redirected to `/tmp` on ephemeral services or to durable storage later. The release registry itself remains immutable:

- `backend/data/connector_operations_registry_v2130.json`

## WordPress surfaces

- Public status: `[sc_public_connector_operations]`
- Administrator-only summary: `[sc_connector_operations_control_center]`

The administrative shortcode is read-only. Live job execution and quarantine resolution remain protected backend actions.

## Governance boundaries

- Credentials, authorization headers, cookies, and complete upstream payloads are never persisted by this control center; raw payloads are never persisted.
- Quarantine stores a bounded, recursively redacted preview only.
- An accepted receipt proves that the configured ingestion contract passed; it does not certify upstream factual accuracy or completeness.
- Public operational status is not a guarantee of real-time coverage.
- Cached and fallback-safe sources remain labeled as such.
- No paid scheduler, queue, database, or connector provider is required by the default release.
