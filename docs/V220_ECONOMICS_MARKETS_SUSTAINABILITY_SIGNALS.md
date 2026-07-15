# Site Intelligence v2.2.0 — Economics, Markets, and Sustainability Signals

Version 2.2.0 adds a public, Core-backed workspace for official economic and sustainability records. The Site Intelligence backend reads the scoped public Core economics API, sanitizes records, and returns only public-safe fields to the browser.

## Public workspace

- Route: `/app/?view=economics`
- WordPress shortcode: `[sc_economics_sustainability_observatory height="1250"]`

## Capabilities

- Macroeconomics, labour, trade, financial conditions, energy, agriculture, demographics, company filings, and sustainability domain filters
- Official-source and geography filters
- Indicator time-series charting
- Latest-observation geographic mapping
- Same-indicator two-geography comparison
- CSV export of the filtered public response
- Shareable URL state and browser-local Saved View integration
- Workbench and Decision Studio handoffs
- Explicit Core connected, degraded, disabled, and unconfigured states

## Market-data boundary

The workspace does not claim that free official-statistics records are licensed real-time exchange feeds. Every normalized record receives one of the supported public timing labels:

- `OFFICIAL RELEASE`
- `LATEST AVAILABLE`
- `DELAYED`
- `END OF DAY`
- `HOURLY`
- `DAILY`
- `WEEKLY`
- `MONTHLY`
- `QUARTERLY`
- `ANNUAL`
- `STALE`

An upstream `real_time` label is not repeated unless an approved future source contract and release explicitly supports it.

## Public endpoints

- `GET /public/economics-sustainability`
- `GET /public/economics-sustainability/records`
- `GET /public/economics-sustainability/facets`
- `GET /public/economics-sustainability/series`
- `GET /public/economics-sustainability/compare`
- `GET /public/economics-sustainability/brief`
- `GET /public/economics-sustainability/diagnostics`

## Security and provenance

- Core credentials remain server-side.
- Sensitive mapping keys and credential-like URL parameters are removed.
- Source URLs must be HTTP or HTTPS.
- Provider metadata is bounded before browser delivery.
- Units, period, frequency, seasonal adjustment, price basis, source, vintage, and attribution remain available.
- Missing records are represented as empty states and are never fabricated from sample market prices.

## Free-provider policy

The release introduces no paid API dependency and no credit-card-required provider. It consumes records already governed by the Core v2.7.3 free-source acceptance gate and delivered through Core v2.8.0.
## Release hardening

Country-, category-, and source-filtered event diagnostics return `unavailable` when an unrelated stale global cache contains no record matching the requested filter. Matching stale evidence remains labeled `stale`.

