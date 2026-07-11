# Sustainable Catalyst Site Intelligence

**Current release:** v1.19.0 — Comparative Intelligence and Briefing Studio

Sustainable Catalyst Site Intelligence is a public-interest observatory for Earth observation, global country indicators, natural hazards, humanitarian reporting, source-aware dashboards, and comparative research.

## Public application

- Standalone app: `https://sustainable-catalyst-site-intelligence.onrender.com/app/`
- Earth Observation: `/app/?view=earth`
- Live Events: `/app/?view=events`
- Global Country Intelligence: `/app/?view=country&country=KEN`
- Comparative Intelligence: `/app/?view=compare&country=KEN&compare=GHA`
- Primary WordPress embed: `[sc_site_intelligence_app height="1000"]`

## v1.19.0 release focus

v1.19.0 replaces the legacy comparison placeholder with a first-class Comparative Intelligence and Briefing Studio in the standalone application.

### Comparative workspace

- Two-country selector using the normalized global country catalog
- Swap, reset, share, and print controls
- Shareable URL state using `country` and `compare`
- Table, chart, map, brief, and export views
- Request cancellation and stale-response protection
- Local loading and failure states
- Duplicate-country prevention

### Methodological comparison contract

The comparison layer calculates a difference only when:

- indicator IDs match
- units match
- both countries have explicitly labeled values
- definitions are aligned

Reporting years remain visible. A year mismatch is labeled rather than silently normalized. Missing values remain explicit as:

> No validated public value is currently available.

The product does not create an unexplained composite score or national ranking.

### Comparative charts and map

- Grouped latest-value presentation in the table
- Synchronized multi-year trend charts
- Common-year counts
- Two-country geographic orientation map
- Accessible tabular information alongside charts
- Clear primary and comparison color keys

### Comparative briefing

The public brief includes:

1. comparison scope
2. country summaries
3. latest available indicators
4. trend series
5. recent public event counts
6. methodological caveats
7. source list
8. generated timestamp
9. responsible-use boundary

### Exports

- JSON evidence manifest
- CSV indicator table
- print-ready HTML brief

Exports preserve values, units, reporting years, compatibility states, calculated differences, source names, source URLs, application version, and methodological boundaries.

### Public endpoints

- `/public/compare`
- `/public/compare/indicators`
- `/public/compare/trends`
- `/public/compare/events`
- `/public/compare/brief`
- `/public/compare/export`

### WordPress

New specialized embed:

```text
[sc_comparative_intelligence country="KEN" compare="GHA" height="1100"]
```

The primary public embed remains:

```text
[sc_site_intelligence_app height="1000"]
```

### v1.18.3 reliability foundation retained

v1.19.0 retains:

- normalized global country names and aliases
- explicit live, cached, stale, reference-snapshot, and unavailable states
- process-memory and JSON last-known-good caching
- abortable country requests
- country diagnostics
- retained country-event match method and confidence
- optional Platform Core integration
- no additional paid infrastructure

## Public diagnostics

### Build compatibility

`GET /public/build-info`

Returns:

- backend version
- API schema version
- expected WordPress plugin version
- release name
- Git commit when supplied by the host
- build timestamp
- Platform Core optional state

### Country catalog diagnostics

`GET /public/countries/diagnostics`

Returns public-safe catalog, coverage, timing, and cache information.

### Country diagnostics

`GET /public/country/{ISO3}/diagnostics`

Returns:

- metadata state
- successful indicator count
- live indicator count
- missing indicator IDs
- trend count
- country-linked event count
- cache state
- stale state
- connector timings
- event timing

Diagnostics do not expose API keys, stack traces, raw retry queues, or private configuration.

## Principal public endpoints

### Comparative Intelligence

- `GET /public/compare?country=KEN&compare=GHA`
- `GET /public/compare/indicators?country=KEN&compare=GHA`
- `GET /public/compare/trends?country=KEN&compare=GHA`
- `GET /public/compare/events?country=KEN&compare=GHA`
- `GET /public/compare/brief?country=KEN&compare=GHA`
- `GET /public/compare/export?country=KEN&compare=GHA&format=json|csv|html`


### Release and health

- `/`
- `/health`
- `/public/build-info`
- `/public/launch-status`
- `/release/public-summary`
- `/release/status`
- `/release/smoke-test`

### Countries

- `/public/countries`
- `/public/countries/search`
- `/public/countries/regions`
- `/public/countries/diagnostics`
- `/public/country/{ISO3}/overview`
- `/public/country/{ISO3}`
- `/public/country/{ISO3}/indicators`
- `/public/country/{ISO3}/trends`
- `/public/country/{ISO3}/brief`
- `/public/country/{ISO3}/evidence-lineage`
- `/public/country/{ISO3}/diagnostics`

### Events

- `/public/events`
- `/public/events/categories`
- `/public/events/sources`
- `/public/events/timeline`
- `/public/events/summary`
- `/public/events/{event_id}`

### Earth Observation

- `/public/earth-observation`
- `/public/earth-observation/layers`
- `/public/earth-observation/compare`
- `/public/earth-observation/timeline`
- `/public/earth-observation/presets`
- `/public/earth-observation/export-manifest`
- `/public/earth-observation/diagnostics`

## WordPress shortcodes

- `[sc_comparative_intelligence country="KEN" compare="GHA" height="1100"]`

Primary product:

```text
[sc_site_intelligence_app height="1000"]
```

Specialized standalone views:

```text
[sc_earth_observation_studio height="1000"]
[sc_live_event_intelligence height="1000"]
[sc_global_country_intelligence country="KEN" height="1100"]
[sc_comparative_intelligence country="KEN" compare="GHA" height="1100"]
```

Legacy compatibility views remain available, but the long-term direction is one main standalone app embed rather than a long stack of demonstration shortcodes.

## Local development

```bash
cd backend
python3 -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8091
```

Open:

- API: `http://127.0.0.1:8091/`
- Docs: `http://127.0.0.1:8091/docs`
- App: `http://127.0.0.1:8091/app/`

## Validation

```bash
cd backend
python3 -m pytest -q
python3 -m compileall -q app
node --check public_app/assets/app.js
php -l ../wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php
```

Expected test result for v1.19.0:

```text
206 passed
```

## Render deployment

The repository includes `render.yaml` for the existing free Render service.

Build command:

```text
pip install -r backend/requirements.txt
```

Start command:

```text
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Platform Core remains optional and disabled by default.

## Responsible-use boundary

Site Intelligence supports research, orientation, source review, public understanding, and documented comparison. It does not replace authoritative records, field investigation, professional environmental analysis, engineering review, legal advice, financial advice, medical advice, regulatory compliance review, emergency instructions, or safety-critical judgment.

## License

MIT. See `LICENSE`.
