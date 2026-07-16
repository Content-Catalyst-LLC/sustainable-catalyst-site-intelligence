# Sustainable Catalyst Site Intelligence v2.13.0

## Connector Operations and Data Ingestion Control Center

Site Intelligence v2.13.0 adds a managed operational layer across 14 existing connector families. The release unifies connector definitions, datasets, refresh schedules, job triggers, execution receipts, freshness, quotas, retries, circuit breakers, schema contracts, transformation declarations, quarantine review, and public-safe status.

### New capabilities

- Unified connector and dataset registry
- Manual, scheduled, and conditional job definitions
- Explicit dry-run-first due-job batch runner
- Execution history with reproducible receipts
- Freshness and expected-update diagnostics
- Credential-readiness checks without exposing credential values
- Per-minute and per-day quota windows
- Bounded retries with exponential backoff
- Circuit-breaker state and force override
- Schema, payload-size, and record-count validation
- Redacted quarantine and resolution records
- Dataset acceptance and digest history
- Token-protected administrative API
- Sanitized public operations endpoint
- Public and administrator-only WordPress shortcodes
- Zero-cost file-backed default with configurable runtime paths

### Public endpoint

`GET /public/connectors/operations`

### Private control center

`GET /admin/connectors/control-center`

### WordPress shortcodes

- `[sc_public_connector_operations]`
- `[sc_connector_operations_control_center]`

### Validation

- 405 backend tests passed
- Release contract validator passed
- Python compilation passed
- JavaScript syntax passed
- WordPress PHP syntax passed
- Registry and JSON manifests passed
- Runtime state, history, quarantine, country cache, Python caches, and pytest caches are excluded from the immutable release manifest

### Important boundary

The application can identify due jobs and execute them through a protected endpoint or CLI runner. It does not claim that a persistent background scheduler exists unless one is separately configured.
