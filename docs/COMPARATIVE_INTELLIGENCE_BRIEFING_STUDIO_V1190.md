# Site Intelligence v1.19.0 — Comparative Intelligence and Briefing Studio

## Purpose

v1.19.0 makes country comparison a first-class public product rather than a legacy shortcode demonstration. The release aligns validated public indicator evidence while retaining reporting years, units, source definitions, delivery states, and methodological limits.

## Public route

```text
/app/?view=compare&country=KEN&compare=GHA
```

## Public API

```text
GET /public/compare
GET /public/compare/indicators
GET /public/compare/trends
GET /public/compare/events
GET /public/compare/brief
GET /public/compare/export
```

All endpoints accept `country` and `compare` ISO parameters. The event endpoint also supports `days` and `limit`. The export endpoint supports `json`, `csv`, and `html`.

## Compatibility rules

A mathematical difference is calculated only when:

- both countries have a value
- indicator IDs match
- units match
- records have an explicit data state
- the definition is aligned

A reporting-year mismatch does not automatically block side-by-side display, but it changes the compatibility state to `different-reporting-years` and adds a visible warning.

## Missing data

Missing values remain visible as unavailable. The system does not convert missing values to zero and does not remove a comparison row merely because one country has no validated record.

## Views

### Table

Shows the indicator, both country values, unit, reporting year, source, data state, compatibility status, calculated difference where valid, and warnings.

### Charts

Shows synchronized multi-year series for the same indicator. Common reporting-year coverage is reported explicitly.

### Map

Shows both country locations for geographic orientation. Map boundaries and labels are not legal or cadastral determinations.

### Brief

Produces a structured public brief containing scope, evidence, trends, event counts, caveats, sources, generation time, and responsible-use boundary.

### Export

- JSON: complete evidence and briefing manifest
- CSV: latest-value indicator comparison
- HTML: print-ready comparison brief

## WordPress shortcode

```text
[sc_comparative_intelligence country="KEN" compare="GHA" height="1100"]
```

The primary Site Intelligence page should continue using the standalone application embed.

## Responsible-use boundary

Comparative Intelligence organizes public evidence for research and orientation. It does not create a national ranking, establish causality, determine eligibility or liability, or replace legal, financial, engineering, environmental, humanitarian, or other professional analysis.
