# Site Intelligence v1.23.0 — Saved Views and Shareable Research Paths

## Purpose

v1.23.0 adds a zero-cost, privacy-preserving way to preserve public Site Intelligence investigations. A saved view records interface configuration and navigation state; it does not copy the underlying evidence payload or create a hosted user profile.

## Public workspace

```text
/app/?view=saved
```

The workspace supports:

- save current public view
- name and locally store a research path
- reopen a saved view
- duplicate a saved view
- copy a public share URL
- export an individual JSON manifest
- export a collection of local manifests
- import and validate individual or collection JSON
- migrate a supported legacy schema
- delete one saved view
- clear all local saved views

## Storage boundary

Saved views use browser `localStorage` under:

```text
sc_site_intelligence_saved_views_v1
```

No account, database, Redis service, hosted profile storage, or additional Render service is introduced. Clearing browser site data removes the locally saved views. They do not synchronize automatically across devices.

## Manifest schema

Current schema:

```text
sc-saved-view/1.0
```

Example:

```json
{
  "schema": "sc-saved-view/1.0",
  "application_version": "1.23.0",
  "id": "sv-example-123456",
  "name": "Kenya climate investigation",
  "view": "thematic",
  "state": {
    "dashboard": "climate-environment",
    "country": "KEN",
    "thematicDays": "30",
    "thematicLayer": "true-color"
  },
  "created_at": "2026-07-11T00:00:00Z",
  "updated_at": "2026-07-11T00:00:00Z"
}
```

## Supported public views

- overview
- Earth observation
- country intelligence
- live event intelligence
- comparative intelligence
- thematic intelligence
- public briefing studio
- source and methodology studio

The Saved Views workspace itself is not a saveable investigation target.

## State restoration

The saved-view layer preserves only registered public fields. Depending on the route, these may include:

- country and comparison country
- active comparison view
- indicator and trend selection
- event date range, category, source, and country filter
- thematic dashboard, country, date range, Earth layer, and trend
- Earth layer, before/after dates, opacity, swipe position, and viewport
- briefing type and public briefing parameters
- source, domain, state, feature, and search filters
- map latitude, longitude, and zoom where applicable

Unsupported fields are removed during validation. Invalid public state falls back safely rather than trapping the application in a loading state.

## Public API

```text
GET  /public/saved-views/schema
POST /public/saved-views/validate
GET  /public/saved-views/migrations
GET  /public/saved-views/diagnostics
```

The POST validation endpoint performs structural validation only. It does not retain the request body or write any user record.

## Validation rules

The backend validates:

- supported schema
- supported public view
- manifest size
- required name and state object
- stable ID format
- ISO-style three-letter country codes
- allowed thematic dashboards
- allowed comparison views
- allowed source states
- allowed briefing types
- dates and numeric ranges
- duplicate comparison-country rejection
- registered public state fields only
- sensitive-looking field rejection

Sensitive field names include API keys, passwords, secrets, tokens, authorization data, cookies, sessions, private URLs, stack traces, environment data, and diagnostics.

## Migration

Supported migration:

```text
sc-saved-view/0.9 → sc-saved-view/1.0
```

Migration rules:

- `route` becomes `view`
- `params` becomes `state`
- `title` becomes `name`
- `saved_at` becomes `created_at`
- unsupported state keys are removed

Unsupported schemas are rejected explicitly.

## Import and export

Individual manifests use `sc-saved-view/1.0`.

Collections use:

```text
sc-saved-view-collection/1.0
```

Each imported view is validated independently. Duplicate IDs receive new local IDs, and duplicate names receive deterministic numeric suffixes. Invalid records in a collection are rejected without preventing valid records from being imported.

## Privacy and safety

Saved views contain public interface state only. They exclude:

- API keys
- authentication data
- cookies or sessions
- private notes
- private connector URLs
- internal diagnostics
- environment variables
- stack traces
- retry queues
- briefing evidence payloads

Share URLs reconstruct public interface state and can be inspected before sharing.

## WordPress

Focused embed:

```text
[sc_saved_research_views height="1000"]
```

Primary full-application embed:

```text
[sc_site_intelligence_app height="1000"]
```

## Infrastructure boundary

Platform Core remains optional. v1.23.0 adds no paid persistence, database, Redis service, account system, proprietary map service, or additional Render service.
