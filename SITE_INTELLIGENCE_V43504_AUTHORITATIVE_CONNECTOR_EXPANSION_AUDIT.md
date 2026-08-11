# Site Intelligence v4.35.4 — Authoritative Connector Expansion II Audit

## Purpose

The Site Intelligence authoritative-data branch treats a workspace source registration as incomplete whenever a usable authoritative machine interface exists but the platform does not retrieve it. v4.35.4 converts a second tranche of registered/verified authorities into actual bounded connector clients while preserving provenance, metric semantics and missing-data truth.

## Expansion II interfaces

| Connector | Authority | Mode | Workspace handoff | Authentication |
|---|---|---|---|---|
| NOAA CO-OPS Data API | NOAA Center for Operational Oceanographic Products and Services | LIVE | Coastal Change / Sea Level | Public |
| NOAA NCEI Access Data Service | NOAA National Centers for Environmental Information | LIVE | Climate | Public Access Data service |
| OBIS API v3 | IOC-UNESCO Ocean Biodiversity Information System | LIVE | Marine Biodiversity / Biodiversity | Public |
| Eurostat Statistics API | Eurostat / European Commission | LIVE | Solid Waste & Circular Materials | Public |
| Soil Data Access | USDA Natural Resources Conservation Service | LIVE | Soils & Land Degradation | Public |

## Retrieval controls

### NOAA CO-OPS

- station identifier required
- product allowlist
- allowed unit and time-zone vocabularies
- explicit ranges must be ordered and no more than 31 days
- datum retained for applicable products
- upstream error payloads become connector errors rather than synthetic data
- source `data`/`predictions`, metadata, flags and nulls remain intact

### NOAA NCEI Access Data

- dataset identifier restricted to bounded safe characters
- ISO date range required and capped at 366 days
- station and datatype filter counts capped
- records remain raw source records with source attributes
- historical observations are not represented as forecasts
- token-gated CDO v2 is explicitly distinct from this public connector

### IOC-UNESCO OBIS

- at least one substantive occurrence filter required
- result count capped at 200
- geometry input restricted to bounded POINT/POLYGON/MULTIPOLYGON WKT
- scientific/taxon/date evidence remains source-bounded
- zero returned records do not establish species absence

### Eurostat

- dataset code validated
- at least one geography/time/dimension filter required
- additional dimensions capped
- raw JSON-stat structure retained
- dimensions, units, geography, time and status metadata are not silently flattened into incompatible claims

### USDA-NRCS Soil Data Access

- exactly one `mukey` or `area_symbol` selector required
- identifiers strictly validated rather than repaired into different values
- maximum row count capped at 200
- only fixed, server-authored SQL templates are submitted
- arbitrary user SQL is not accepted
- SSURGO map units remain generalized survey information

## Audit classification precision

The audit previously used host-level implementation evidence for many connectors. That is safe for dedicated API hosts such as `api.obis.org`, but it can over-credit a multipurpose host. NOAA NCEI is now interface-specific: only registrations using the connected Access Data Service prefix receive LIVE implementation evidence from this connector.

This correction removes false positives from unrelated NCEI bathymetry, ocean-exploration and other catalog pages.

## Coverage change

| Measure | v4.35.3.1 baseline | v4.35.4 |
|---|---:|---:|
| Source registrations | 179 | 179 |
| Machine-readable registrations | 96 | 96 |
| Implemented/discovery/config-gated | 50 | 56 |
| LIVE | 32 | 38 |
| DISCOVERY | 8 | 8 |
| REGISTERED / not retrieved | 56 | 50 |
| AUTH_REQUIRED | 10 | 10 |
| BULK | 4 | 4 |
| STALE | 0 | 0 |

The Expansion II connector layer adds five actual interfaces. Six existing registrations become implementation-backed because one connector may satisfy more than one compatible registry entry. The NCEI precision repair prevents unrelated same-host registrations from being counted as live.

## Combined connector catalog

The public authoritative connector catalog contains ten interfaces:

### Expansion I — preserved

- USGS Water Data OGC — LIVE
- NOAA CoastWatch ERDDAP — LIVE
- NASA Exoplanet Archive TAP — LIVE
- UNHCR Refugee Statistics — LIVE
- NASA CMR Collections — DISCOVERY

### Expansion II — new

- NOAA CO-OPS — LIVE
- NOAA NCEI Access Data — LIVE
- IOC-UNESCO OBIS — LIVE
- Eurostat Statistics — LIVE
- USDA-NRCS Soil Data Access — LIVE

Combined catalog state: **9 LIVE + 1 DISCOVERY**.

## Deployment/source-health boundary

v4.35.4 preserves v4.35.3.1 release-gate hardening. Deterministic deployment readiness performs no external source probes. Upstream availability is operational evidence and is non-blocking for promotion.

This matters more as the connector count grows: a NOAA, NASA, USGS, UNHCR, OBIS, Eurostat or USDA outage must not invalidate an otherwise correct Site Intelligence deployment.

## Recommended Expansion III targets

The audit currently prioritizes:

1. USFWS National Wetlands Inventory services — Wetlands & Inland Waters
2. EPA ECHO — industrial/waste/water regulatory evidence
3. NASA FIRMS — wildfire detections with credential/configuration handling
4. USDA NASS Quick Stats — agriculture statistics with API-key gating
5. NASA CMR GraphQL — deeper cross-resource discovery where useful

These should be implemented only where the official machine interface, source semantics, authentication requirements and bounded-query behavior can be preserved.
