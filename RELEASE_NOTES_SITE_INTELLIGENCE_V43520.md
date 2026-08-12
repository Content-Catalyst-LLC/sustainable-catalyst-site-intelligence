# Site Intelligence v4.35.20 — Country-Linked Record Recovery, Source-Bounded Filtering & Humanitarian Discovery

## Release objective
Repair the country-linked record path so a supported country—especially Palestine (`PSE`)—does not appear to have no linked public records merely because a small global event batch omitted its records or a credential-gated provider is unavailable.

## Delivered
- Added `/public/country/{country_code}/linked-records` as the country workspace's dedicated linked-record contract.
- Changed ReliefWeb retrieval from global-batch-then-local-filtering to source-bounded country retrieval using ISO3 when a country is selected.
- Preserved the configured ReliefWeb `appname` requirement and expose missing configuration as `configuration-required` rather than silently treating it as a healthy empty source.
- Added credential-free HDX/OCHA dataset discovery as a recovery lane for country-linked public humanitarian metadata.
- Kept HDX dataset discovery semantically distinct from events, reports, observations, incidents, and current operating conditions.
- Added explicit country-match evidence, source identity, record class, evidence class, limitations, and source state to linked records.
- Changed the country workspace from the hazard-oriented `/public/events` contract to the new country-linked record contract.
- Changed the country workspace handoff from “Open event explorer” to “Open humanitarian view.”
- Added a deterministic, network-free `/public/country-linked-records/readiness` release control plane.
- Kept external provider health non-blocking for release promotion.

## Palestine repair
For `PSE`, Site Intelligence now asks country-capable humanitarian sources for Palestine-bounded records instead of hoping Palestine appears inside a small global batch. When ReliefWeb is not configured or is temporarily unavailable, the country-linked record service can retain explicitly Palestine-matched HDX/OCHA discovery records without representing those metadata records as live humanitarian conditions.

A zero-record response is explicitly interpreted as “no matching record was retained from currently connected sources,” not “no event or humanitarian condition exists.”

## Evidence boundaries
- `event-or-report` and `dataset-discovery` are separate record classes.
- HDX dataset metadata is discovery evidence, not proof that a described condition is current.
- A dataset's country tag/title/metadata can establish country linkage; it does not establish incident severity, operational status, or present-day conditions.
- Missing ReliefWeb configuration is a source-configuration state, not evidence of zero humanitarian activity.
- External upstream success or failure does not determine first-party release validity.

## Release invariants
- v4.35.19 deterministic production soak remains inherited and release-blocking.
- v4.35.19 semantic truth boundaries remain inherited.
- Country-linked readiness performs no real upstream network calls.
- Live external provider health remains non-blocking.
- The six-area / 35-route browser architecture remains unchanged.
