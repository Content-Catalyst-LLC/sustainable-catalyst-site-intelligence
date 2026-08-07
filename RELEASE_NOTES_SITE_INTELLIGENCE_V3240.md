# Site Intelligence v3.25.0 — Global Data Truth Control Plane

## Release purpose

v3.25.0 turns the source-level, country-level, and record-level truth layers into one operational control plane. It is a consolidation release: it adds no new public data provider and makes no new live-data claim.

## Public contracts

- `GET /public/data-truth/control-plane`
- `GET /public/data-truth/control-plane/sources`
- `GET /public/data-truth/control-plane/source/{feed_id}`
- `GET /public/data-truth/control-plane/history`
- `GET /public/data-truth/control-plane/schema-drift`
- `GET /public/data-truth/control-plane/outages`
- `GET /public/data-truth/control-plane/coverage`
- `GET /public/data-truth/control-plane/workspaces`
- `GET /public/data-truth/control-plane/export`

## Operational model

Each registered source is classified as operational, degraded, review, unavailable, or unknown from disclosed retrieval, presentation, schema, circuit-breaker, completeness, and success metadata. The classification does not establish accuracy, authority, or country-level record availability.

The history endpoint derives status events only from currently disclosed timestamps and the release snapshot. It explicitly states that it is not a complete historical event log.

The outage register is an attention register. It does not claim that an upstream publisher is globally offline and does not automatically change configuration or publish an outage notice.

## Interface

Data Truth now includes a fourth **Control plane** tab with:

- Source-operation summary
- Source filtering
- Current attention register
- Schema-drift register
- Cross-workspace truth status for the selected country
- Control-plane fingerprint
- JSON export

## Preserved boundaries

- Geographic eligibility is not observed coverage.
- Source health is not record truth.
- Unknown remains unknown.
- Missing values remain missing.
- Cached, historical, demonstration, and context-only states are not presented as live.
- Fingerprints detect changes to normalized disclosures and are not certifications of source accuracy.
