# Site Intelligence v1.20.0 — Public Briefing and Export Studio

## Purpose

v1.20.0 turns Site Intelligence from a collection of exploratory public views into a documented research-output system. The release introduces one canonical investigation manifest that can describe country, comparison, event, Earth-observation, and thematic research states without inventing unavailable evidence or requiring Platform Core.

The Public Briefing and Export Studio is deterministic. It assembles retrieved evidence, source identity, geography, dates, filters, delivery states, missing-data records, methodology, and interpretation boundaries into a reproducible public brief.

## Standalone route

```text
/app/?view=briefing&briefType=country&country=KEN
```

Supported `briefType` values:

- `country`
- `comparison`
- `event`
- `earth`
- `thematic`

## Canonical investigation manifest

Every brief uses schema:

```text
sc-public-briefing/1.0
```

The manifest includes:

- application and schema version
- methodology version
- stable brief ID derived from selected state
- brief type
- title and summary
- research scope
- URL-restorable state
- geography
- selected dates
- filters
- indicators
- trend records
- event records
- Earth-observation layers
- thematic evidence items
- source records and URLs
- live, cached, stale, fallback, reference, and unavailable states
- explicit missing-data records
- methodology notes
- interpretation limits
- responsible-use boundary
- export capabilities

The stable brief ID does not depend on the generation timestamp. Recreating the same selected state produces the same identifier while preserving a fresh `generated_at` value.

## Brief types

### Country Intelligence Brief

Combines:

- normalized country identity
- latest valid indicator records
- reporting years and units
- trend coverage
- recent country-linked public events
- source URLs
- cache and delivery states
- missing indicator records
- country interpretation limits

Zero remains a valid value and is not treated as unavailable.

### Country Comparison Brief

Combines:

- two normalized country records
- latest aligned indicator evidence
- source, unit, year, definition, and state compatibility
- mathematical differences only where comparison rules permit them
- trend compatibility and coverage
- public-event context
- conflict and missing-data records
- comparison methodology

A comparison with mismatched reporting years remains visible but does not receive a mathematical difference.

### Event Situation Brief

Supports either:

- one public event selected by source event ID, or
- a filtered situation view using date window, country, category, and source

The brief preserves event time, publication time, source, location, country-match method, and confidence where available. Event feed failures remain local and do not block the rest of Site Intelligence.

### Earth Observation Brief

Documents:

- selected layer
- before and after dates
- map center
- zoom
- opacity
- source
- attribution
- observation type
- layer limitations
- comparison boundary

The manifest documents the requested map state. It does not certify that every requested tile rendered or that imagery represents ground truth.

### Thematic Intelligence Brief

Packages a cross-domain dashboard state with:

- dashboard identity
- selected country and comparison context
- optional date range
- evidence domains
- source registry
- current evidence states
- source-dependent data gaps
- methodology and dashboard interpretation boundaries

## Public endpoints

### Directory

```text
GET /public/briefing-studio
```

Returns brief types, export formats, routes, schema, methodology version, and public boundaries.

### Generate brief

```text
GET /public/briefing-studio/brief
```

Examples:

```text
/public/briefing-studio/brief?type=country&country=KEN
/public/briefing-studio/brief?type=comparison&country=KEN&compare=GHA
/public/briefing-studio/brief?type=event&country=KEN&days=30
/public/briefing-studio/brief?type=earth&layer_id=true-color&date_a=2026-07-01&date_b=2026-07-10
/public/briefing-studio/brief?type=thematic&dashboard_id=climate-human-vulnerability&country=KEN
```

### Export

```text
GET /public/briefing-studio/export
```

Server formats:

- `json`
- `csv`
- `html`

Example:

```text
/public/briefing-studio/export?type=country&country=KEN&format=json
```

Export responses use:

```text
Cache-Control: no-store
X-Content-Type-Options: nosniff
```

### Diagnostics

```text
GET /public/briefing-studio/diagnostics
```

Returns public-safe builder and export readiness without exposing keys, stack traces, private configuration, or retry queues.

## Export behavior

### JSON

The JSON export contains the complete investigation manifest plus an export manifest containing filename, format, application version, schema version, methodology version, and generation timestamp.

### CSV

CSV flattens evidence into rows and includes:

- brief ID
- brief type
- evidence group
- record type
- record ID
- label
- comparison side
- country code and name
- value
- unit
- reporting year
- observed time
- source name
- source ID
- source URL
- data state
- compatibility
- notes

CSV uses a UTF-8 BOM, consistent line endings, and spreadsheet-formula safeguards.

### HTML

HTML is the print-first document format. It includes:

- brief title and summary
- brief ID
- application, schema, and methodology versions
- selected scope
- evidence table
- source links
- missing-data records
- methodology
- interpretation limits
- responsible-use boundary
- print-visible source URLs

PDF remains deferred until the print-ready HTML format is stable across production browsers.

### PNG

PNG capture is generated in the browser with `html2canvas`. It captures the rendered brief panel and visible attribution. It is a visual record of the interface, not an authoritative source artifact. The JSON or HTML export should accompany consequential use.

## WordPress shortcode

```text
[sc_public_briefing_studio type="country" country="KEN" height="1150"]
```

Comparison example:

```text
[sc_public_briefing_studio type="comparison" country="KEN" compare="GHA" height="1200"]
```

Earth example:

```text
[sc_public_briefing_studio type="earth" layer_id="true-color" date_a="2026-07-01" date_b="2026-07-10" height="1200"]
```

The primary public embed remains:

```text
[sc_site_intelligence_app height="1000"]
```

## Reliability principles

- Missing data remains visible.
- Optional event failure remains local.
- Brief generation does not require Platform Core.
- No paid database, Redis service, proprietary map service, or additional Render service is introduced.
- Source URLs remain available in machine-readable and print-ready exports.
- Brief state is URL-restorable.
- Superseded browser requests are cancelled.
- The browser UI removes loading state in `finally`.
- Server exports use deterministic schemas and safe filenames.
- PDF is not advertised before print HTML is stable.

## Responsible-use boundary

The studio supports orientation, research, source review, and documentation. It does not replace authoritative records, field investigation, emergency information, environmental assessment, engineering review, legal advice, financial advice, regulatory compliance review, humanitarian operations, or other qualified professional judgment.
