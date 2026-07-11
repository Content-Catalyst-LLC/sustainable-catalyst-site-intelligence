# Sustainable Catalyst Site Intelligence

**Current release:** v1.18.3 — Global Country Reliability, Data Coverage, and Release Integrity

Sustainable Catalyst Site Intelligence is a public-interest observatory for Earth observation, global country indicators, natural hazards, humanitarian reporting, source-aware dashboards, and comparative research.

## Public application

- Standalone app: `https://sustainable-catalyst-site-intelligence.onrender.com/app/`
- Earth Observation: `/app/?view=earth`
- Live Events: `/app/?view=events`
- Global Country Intelligence: `/app/?view=country&country=KEN`
- Primary WordPress embed: `[sc_site_intelligence_app height="1000"]`

## v1.18.3 release focus

v1.18.3 stabilizes the global country layer before Comparative Intelligence is built.

### Release integrity

- One canonical backend version in `backend/app/version.py`
- Public-safe `/public/build-info` compatibility endpoint
- Matching backend and WordPress plugin version: `1.18.3`
- WordPress administrator warning when plugin and backend versions differ
- Updated release status, launch status, README, CHANGELOG, and documentation
- 199 backend tests passing

### Country catalog reliability

- Public display-name normalization without altering source records
- Source names retained as `source_name`
- Alternate names retained for search
- Whitespace-normalized regions
- ISO2, ISO3, display-name, source-name, and alias search
- Explicit country-or-territory classification
- Graceful frontend fallback to Kenya for an unsupported URL country code

Examples:

- `Egypt, Arab Rep.` → `Egypt`
- `Korea, Rep.` → `South Korea`
- `Korea, Dem. People's Rep.` → `North Korea`
- `Russian Federation` → `Russia`
- `Congo, Dem. Rep.` → `Democratic Republic of the Congo`

### Indicator reliability

Each indicator retains:

- indicator ID
- value
- unit
- reporting year
- source name
- source URL
- retrieved time
- data state
- stale state
- Platform Core lineage state where enabled

Data states include:

- `live`
- `partial-live`
- `cached`
- `stale`
- `reference-snapshot`
- `unavailable`

Zero remains a valid value and is never treated as missing.

### Zero-cost caching

Country catalog and World Bank series use:

1. process-memory caching
2. atomic JSON last-known-good caching
3. explicit retrieval time
4. explicit stale state
5. bounded in-process memoization

Default cache file:

`backend/data/country_last_known_good.json`

The JSON cache is a best-effort runtime cache on Render's ephemeral filesystem. It improves resilience across ordinary process restarts but is not guaranteed to survive a new deploy or infrastructure replacement. No Redis, paid database, or second Render service is required.

Optional override:

```env
SC_SI_COUNTRY_CACHE_PATH=/path/to/country_last_known_good.json
```

### Race-safe browser behavior

The standalone country experience now includes:

- `AbortController` cancellation for superseded requests
- request-sequence validation
- 12-second request timeout
- retry behavior that does not retry aborted requests
- 320 ms country-search debounce
- stale chart and card clearing before a new country loads
- one country map marker at a time
- local retry controls
- no blank screen for unsupported country codes

### Country-event matching evidence

Country-linked event records now retain:

```json
{
  "country_code": "KEN",
  "country_match_method": "source-country-field",
  "country_match_confidence": 0.99,
  "country_match_evidence": "Kenya"
}
```

Matching can use:

- source country fields
- country names and aliases in titles
- a limited coordinate bounding-box match for priority countries
- explicit demonstration-fixture labeling for fallback records

A matched event should not be interpreted more strongly than its retained method and confidence allow.

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

Primary product:

```text
[sc_site_intelligence_app height="1000"]
```

Specialized standalone views:

```text
[sc_earth_observation_studio height="1000"]
[sc_live_event_intelligence height="1000"]
[sc_global_country_intelligence country="KEN" height="1100"]
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

Expected test result for v1.18.3:

```text
199 passed
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
