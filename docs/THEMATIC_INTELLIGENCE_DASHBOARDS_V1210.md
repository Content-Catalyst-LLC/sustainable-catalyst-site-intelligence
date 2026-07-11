# Site Intelligence v1.21.0 — Thematic Intelligence Dashboards

## Purpose

This release turns existing country, event, Earth-observation, comparison, and briefing infrastructure into four focused, source-aware public products.

## Dashboards

### Climate and Environment

Combines emissions, water, electricity-access context, environmental Earth-observation layers, and recent natural-hazard records.

### Human Development

Combines population, health, education, water, electricity, income, inequality, trends, and public-event context.

### Human Security

Combines public events, humanitarian and displacement context, essential-service indicators, and mapped evidence without producing a threat or fragility score.

### Infrastructure and Connectivity

Combines electricity, water, population, economic, nighttime-light, Earth-observation, and recent event context.

## Shared product contract

Each dashboard provides a map, latest-value cards, historical trends, accessible trend tables, event context, Earth layers, sources, methodology, explicit missing-data records, responsible-use boundaries, briefing handoff, and JSON/CSV/HTML exports.

## Reliability rules

- Missing indicators remain local to their cards.
- Optional event-source failures do not disable the dashboard.
- Trend gaps are not silently interpolated.
- Values retain source, unit, reporting year, retrieval state, and stale state.
- No proprietary composite score or unexplained ranking is produced.
- Country or dashboard changes cancel superseded requests and reject stale responses.
- Shared URLs preserve dashboard, country, event window, and selected layer.

## Public routes

- `/public/thematic-dashboards`
- `/public/thematic-dashboard/{dashboard_id}`
- `/public/thematic-dashboard/{dashboard_id}/indicators`
- `/public/thematic-dashboard/{dashboard_id}/trends`
- `/public/thematic-dashboard/{dashboard_id}/events`
- `/public/thematic-dashboard/{dashboard_id}/brief`
- `/public/thematic-dashboard/{dashboard_id}/export`
- `/public/thematic-dashboard/{dashboard_id}/diagnostics`

## WordPress

`[sc_thematic_intelligence dashboard="climate-environment" country="KEN" height="1150"]`

The standalone application remains the primary public product. Platform Core remains optional.
