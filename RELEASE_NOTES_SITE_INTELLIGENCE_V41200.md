# Site Intelligence v4.13.0 — Marine Human Activity, Protected Areas & Maritime Pressure

## Release purpose

v4.13.0 extends the ocean environment from physical and biological observation into human-use and conservation context without creating a new primary workspace or public route family.

The ocean continuum is now:

**Ocean Surface → Water Column → Seafloor → Underwater Observation → Biodiversity → Missions → Events & Ecosystem Change → Human Activity & Protection**

The v4 architecture remains **six primary areas / 35 public routes**.

## Source architecture

- **NOAA / BOEM Marine Cadastre Vessel Traffic** — AIS-derived vessel traffic and ocean-planning context.
- **NOAA Marine Protected Areas Inventory** — source-reported MPA boundaries and management/classification attributes in U.S. waters.
- **EMODnet Human Activities** — interoperable European layers across shipping, ports, offshore energy, aquaculture, cables/pipelines, extraction/disposal, and related activities.
- **Global Fishing Watch APIs** — vessel and ocean-activity products, including algorithmically inferred fishing activity, subject to upstream access and terms.

## Evidence classes

**AIS position · vessel track · vessel density · inferred fishing activity · infrastructure feature · aggregate activity · protected-area boundary · management attribute · restriction attribute**

## Truth boundaries

- AIS is not a complete vessel census.
- Zero returned AIS records are not represented as proof that no vessel was present.
- Inferred fishing activity is not represented as illegal fishing.
- Protected-area overlap is not represented as a legal violation, enforcement finding, or navigational instruction.
- Infrastructure is not assumed active or current without source support.
- Temporal and spatial mismatches remain visible.
- Upstream credentials are never embedded in public browser state or repository fixtures.

## New public contracts

```text
GET  /public/marine-human-activity
GET  /public/marine-human-activity/catalog
GET  /public/marine-human-activity/state

POST /public/marine-human-activity/activity/normalize
POST /public/marine-human-activity/protected-area/normalize
POST /public/marine-human-activity/overlap/preview

GET  /public/marine-human-activity/export-manifest
GET  /public/marine-human-activity/readiness
```

## Interface

The ocean sequence gains a deferred **Human activity & protection** environment after Ocean Events. Its central label is:

> **SPATIAL ORIENTATION · NOT A COMPLIANCE FINDING**

## Compatibility

v4.13.0 preserves the six-area / 35-route v4 architecture and does not alter the existing country selector, WordPress host-page isolation contract, fixed application viewport, or prior ocean/space evidence boundaries.

## Packaging repair revision — 2026-08-09

The first local installer run exposed a release-packaging defect before GitHub/Render promotion: the immutable manifest had accidentally frozen runtime-only files under `backend/backend/data/`. The first deterministic test pass updated that runtime state, causing the second manifest verification to fail as designed.

The corrected v4.13.0 package:

- excludes the erroneous nested `backend/backend/` runtime tree from the immutable manifest;
- removes nested runtime state from the distributable repository;
- extends test hygiene to clean both canonical and backend-relative runtime locations;
- adds a dedicated v4.13.0 manifest builder and static regression assertion preventing nested runtime state from being frozen again;
- preserves the application version, feature contracts, six-area / 35-route architecture, and WordPress package.

No v4.13.0 GitHub or Render promotion occurred before this repair.
