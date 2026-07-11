# Site Intelligence v1.19.1 — Comparison Reliability Patch

## Purpose

v1.19.1 hardens the two-country Comparative Intelligence and Briefing Studio without broadening the product surface. The release focuses on methodological compatibility, partial-data behavior, chart gaps, export completeness, mobile layout, URL restoration, and local failure states.

## Compatibility model

Each indicator row reports:

- availability for both, one, or neither country
- indicator-definition compatibility
- normalized-unit compatibility
- source-ID and source-family compatibility
- supported data-state status
- reporting-year alignment
- display-comparability
- calculation eligibility
- explicit warnings and methodology flags

Values can be displayed side by side when meaningful, but a mathematical difference is produced only when the definition, unit, source family, data state, and reporting year align.

## Trend model

Trend records include cleaned series, union-year alignment, common years, gap years, chartability, source attribution, coverage, and an explicit non-chartable reason. The public interface provides both a visual chart and an accessible year-by-year table.

## Failure isolation

Country indicators and trends remain usable when one or both optional event requests fail. Event panels return a local `temporarily-unavailable` state rather than failing the comparison route.

## Exports

JSON, CSV, and HTML exports retain source IDs, URLs, units, years, data states, warnings, compatibility, and responsible-use boundaries. CSV output includes spreadsheet-injection safeguards. HTML output includes print-visible source URLs.

## Public routes

- `/public/compare`
- `/public/compare/indicators`
- `/public/compare/trends`
- `/public/compare/events`
- `/public/compare/brief`
- `/public/compare/export`
- `/public/compare/diagnostics`

## WordPress

```text
[sc_comparative_intelligence country="KEN" compare="GHA" view="table" height="1100"]
```

Optional attributes:

- `view`: `table`, `chart`, `map`, `brief`, or `export`
- `indicator`: a public indicator ID such as `SP.POP.TOTL`

## Infrastructure boundary

Platform Core remains optional. No paid database, Redis service, proprietary map service, or additional Render service is required.
