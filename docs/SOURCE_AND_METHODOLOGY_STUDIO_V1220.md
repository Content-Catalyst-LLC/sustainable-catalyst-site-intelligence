# Site Intelligence v1.22.0 — Source and Methodology Studio

## Purpose

Source and Methodology Studio makes the public evidence architecture behind Site Intelligence inspectable. It documents the providers, connectors, coverage, delivery states, feature usage, known limits, and evidence-handling rules used by the country, comparison, event, Earth-observation, thematic, and briefing products.

The studio is a transparency layer. It does not certify source completeness, currentness, legal status, scientific validity for a specific use, or fitness for a consequential decision.

## Standalone route

```text
/app/?view=sources
```

Shareable filters include:

- `source`
- `domain`
- `state`
- `feature`
- `query`

Example:

```text
/app/?view=sources&source=world-bank&feature=compare
```

## Public source registry

The v1.22.0 registry includes:

1. World Bank Open Data
2. NASA EOSDIS Global Imagery Browse Services
3. USGS Earthquake Hazards Program
4. NASA EONET
5. ReliefWeb
6. NASA POWER
7. OpenStreetMap
8. optional Sustainable Catalyst Platform Core provenance integration

Each public record includes:

- stable source ID
- source and publisher name
- authority classification
- domains and data types
- connector type
- update frequency
- public delivery state
- license context
- geographic coverage
- temporal coverage
- feature usage
- official URL
- known limits
- related methodology records

## Public connector states

The studio uses the following public-safe states:

- **Live** — the backend recently retrieved or verified the public source successfully.
- **Cached** — a recently retrieved public record is being served from cache.
- **Stale** — a last-known-good record exists outside the normal freshness window.
- **Temporarily unavailable** — the source did not complete the latest public-safe check.
- **Experimental** — the connector or layer is public but still under availability, schema, or interpretation review.
- **Disabled** — the source is registered but intentionally inactive in the public app.

Delivery state does not describe the substantive age of an indicator. A live API response can still contain an older reporting year.

## Methodology registry

The registry documents actual system behavior for:

- latest valid indicator selection
- missing-value handling
- zero versus unavailable
- live, cached, stale, reference, experimental, and unavailable states
- trend construction
- reporting-year differences
- comparison compatibility
- country-name normalization
- country-event matching
- event deduplication
- Earth-observation date validation
- imagery interpretation
- comparison calculations
- deterministic brief generation
- export generation
- last-known-good caching
- optional-source failure isolation

Every method record includes applicable features, implementation references, rules, known limits, and related source IDs.

## Public API

### Source registry

```text
GET /public/sources
GET /public/sources/{source_id}
GET /public/sources/{source_id}/status
GET /public/sources/{source_id}/coverage
```

Supported registry filters:

```text
/public/sources?domain=human-development
/public/sources?state=live
/public/sources?feature=thematic
/public/sources?query=nasa
/public/sources?include_health=true
```

### Methodology

```text
GET /public/methodology
GET /public/methodology/{method_id}
```

Supported methodology filters:

```text
/public/methodology?feature=compare
/public/methodology?query=missing
```

### Diagnostics and export

```text
GET /public/source-methodology/diagnostics
GET /public/source-methodology/export?format=json
GET /public/source-methodology/export?format=csv
```

## Public-safe diagnostics

The diagnostics endpoint checks:

- required flagship source records are complete
- all source records include authoritative URLs
- all source records include known limitations
- source-to-methodology references resolve
- methodology-to-source references resolve
- public state vocabulary is complete
- no secret-bearing fields are exposed
- Platform Core remains optional

When live connector diagnostics are available, they are converted into public-safe source states. Optional failures remain local and do not disable the source registry.

## Exports

### JSON

The JSON export includes:

- application version
- schema version
- methodology version
- source records
- methodology records
- public-state definitions
- hidden-field policy
- responsible-use boundary

### CSV

The CSV export includes source identity, publisher, state, connector, domains, data types, geographic and temporal coverage, update frequency, license context, official URL, feature usage, known limits, and retrieval metadata.

CSV output uses UTF-8 and guards against spreadsheet formula execution.

## WordPress

Primary source studio shortcode:

```text
[sc_source_methodology_studio height="1100"]
```

Focused source:

```text
[sc_source_methodology_studio source="world-bank" height="1000"]
```

Filtered source view:

```text
[sc_source_methodology_studio domain="events" state="live" height="1100"]
```

The flagship WordPress page should continue using the full standalone application:

```text
[sc_site_intelligence_app height="1000"]
```

## Privacy and security boundary

The public studio does not expose:

- API keys
- secret environment variables
- private connector URLs
- internal stack traces
- authentication details
- raw retry queues
- private diagnostics
- unpublished source-review notes

## Infrastructure boundary

Platform Core remains optional. The release adds no paid database, Redis service, proprietary map service, or additional persistent Render service.
