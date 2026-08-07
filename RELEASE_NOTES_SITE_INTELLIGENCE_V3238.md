# Site Intelligence v3.25.0 — Record Provenance and Indicator Truth

## Purpose

This release extends Data Truth from country/source summaries to the individual public record a visitor is inspecting. Indicators, map layers, events, charts, and table records can now disclose source, dates, units, transformations, geographic context, limitations, and a deterministic record fingerprint.

## New public contracts

- `GET /public/record-truth/country/{ISO3}`
- `GET /public/record-truth/indicator/{ISO3}/{indicator_id}`
- `GET /public/record-truth/map-layer/{layer_id}`
- `POST /public/record-truth/resolve`
- `GET /public/record-truth/manifest?country={ISO3}`

## Application changes

- Added a Record Truth drawer available from country indicators, the active imagery layer, and event records.
- Added record JSON export and a country provenance-manifest export.
- Added truth states for observed, historical snapshot, contextual, missing, unverified, and unavailable records.
- Preserved missing values without imputation or cross-country substitution.
- Added source-safe URL normalization and explicit transformation ledgers.
- Added SHA-256 fingerprints over canonical disclosed records. A fingerprint detects a disclosure change; it does not certify the publisher, measurement, or conclusion.

## Compatibility and safeguards

- Preserves Global Country Data Truth and the coverage matrix.
- Preserves the focus-safe 173-country selector.
- Preserves shell-first startup, serialized routes, service-worker closure, and fixed WordPress embed isolation.
- Adds direct and WordPress-iframe Chromium gates for map-layer, indicator, and event truth.
