# Site Intelligence v4.35.20 — Country-Linked Record Recovery Audit

## Defect
The country workspace rendered “Country-linked records” from `/public/events?country_code=...`. The event aggregator loaded a bounded global ReliefWeb batch and filtered by country afterward. A country could therefore have valid upstream records yet render an empty panel because none landed in that global batch. If ReliefWeb's required application identifier was absent, the remaining USGS/EONET event feeds were not a sufficient humanitarian record path for countries such as Palestine.

## Repair
### 1. Country-bounded source acquisition
`unified_live_events._reliefweb_reports()` accepts a country code and applies an upstream `country.iso3` filter. The cache key includes country scope, preventing country-specific retrieval from aliasing a global batch.

### 2. Explicit source configuration state
A missing ReliefWeb application identifier maps to `configuration-required`. It is not flattened into a healthy empty result.

### 3. Dedicated linked-record contract
`country_linked_records_v43520.py` builds a country-linked record response from:
- operational/public event or report records returned by the country-bounded event path; and
- explicitly country-matched HDX/OCHA public dataset discovery metadata.

### 4. Semantic separation
Every retained item declares `record_class` and `evidence_class`. HDX metadata is `dataset-discovery` / `discovery-metadata`; it cannot be promoted into a live event, report, incident, current observation, or service-condition statement.

### 5. Country-match discipline
HDX discovery candidates must contain an explicit ISO3 or country-name/alias match before retention. A search hit alone is insufficient.

### 6. Honest empty state
Zero retained records means only that the currently connected sources returned no retained country-linked record. It is never interpreted as zero incidence, zero humanitarian need, or absence of a real-world condition.

## Release health
`/public/country-linked-records/readiness` is deterministic and network-free. The v4.35.20 deployment verifier requires the linked-record recovery contract while retaining the inherited policy that live upstream provider health is non-blocking for release promotion.

## Scope boundary
This release repairs acquisition, routing, presentation, and source-state semantics. It does not claim that every humanitarian authority has been integrated, that every HDX dataset is current, or that discovery metadata replaces operational OCHA/WHO/sector reporting. Those remain separate evidence integrations.
