# Site Intelligence v4.35.2 — Authoritative API & Workspace Integrity Audit

## Purpose

This release pauses domain expansion and makes authoritative data connectivity an explicit Site Intelligence platform contract. A source appearing in a workspace is no longer treated as equivalent to a live connector.

## Authoritative API inventory

v4.35.2 inventories source-bearing domain registries and the legacy live external-connector registry, then classifies each registration as:

- **LIVE** — implemented record/observation retrieval path and required configuration present.
- **DISCOVERY** — live metadata/capability discovery, but not underlying observation retrieval.
- **REGISTERED** — machine-readable authoritative source is known, but Site Intelligence does not yet retrieve it.
- **AUTH_REQUIRED** — retrieval is implemented/viable but credentials or approved configuration are required.
- **BULK** — authoritative machine-readable files exist but are not connected as a live service.
- **STALE** — implemented endpoint/version is obsolete or decommissioned.
- **UNAVAILABLE** — the current source record does not document a stable machine-readable path.

The audit is deterministic and does not call upstream providers when the release is validated.

## ReliefWeb V2 migration

The humanitarian live-events connector now uses ReliefWeb API V2. V1 is no longer referenced by the active connector. Live ReliefWeb retrieval is disabled until the server has a pre-approved ReliefWeb `appname`:

```text
SC_SI_RELIEFWEB_APPNAME=<approved appname>
```

No appname value is exposed in public diagnostics.

## New public contracts

- `GET /public/authoritative-apis`
- `GET /public/authoritative-apis/catalog`
- `GET /public/authoritative-apis/workspaces`
- `GET /public/authoritative-apis/readiness`

The Sources & Methodology workspace now displays authoritative API registration coverage, implemented/discovery coverage, connector gaps, configuration-gated sources, and priority connector targets.

## Initial verified connector-expansion targets

- USGS Water Data OGC APIs
- NOAA CoastWatch ERDDAP
- NASA EOSDIS CMR Search / GraphQL
- NASA Exoplanet Archive TAP / ADQL
- UNHCR Refugee Statistics API

These are explicitly represented as backlog targets until actual retrieval clients exist; verification of an upstream machine interface does not promote it to LIVE.

## Preserved reliability work

- Palestine remains canonical for `PSE` / `PS` and all supported aliases.
- Platform Core configuration-readiness diagnostics remain intact.
- Six primary areas and all 35 public routes remain intact.
- Missing observations remain missing and are not replaced by sample values in the audit layer.
