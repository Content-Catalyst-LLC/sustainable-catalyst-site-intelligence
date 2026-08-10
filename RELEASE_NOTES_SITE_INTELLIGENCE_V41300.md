# Site Intelligence v4.13.0 — Marine Pollution, Debris & Water-Quality Intelligence

## Release scope

v4.13.0 extends the existing Earth Observation ocean continuum without adding a primary navigation area or public workspace route:

**Ocean Surface → Water Column → Seafloor → Underwater Observation → Biodiversity → Missions → Events & Ecosystem Change → Human Activity & Protection → Pollution, Debris & Water Quality**

The six-area / 35-route v4 architecture remains unchanged.

## Source registry

The initial source registry contains four distinct evidence families:

- **NOAA NCEI Marine Microplastics** — aggregated global marine microplastics observations with sampling context and provenance.
- **EMODnet Chemistry** — harmonized marine chemistry, contaminants, eutrophication/acidity, and marine-litter products with interoperable web-service access.
- **Copernicus Marine Biogeochemistry** — modeled, analyzed, forecast, reanalysis, and in-situ biogeochemical products including nutrients, dissolved oxygen, chlorophyll, pH, and carbon-system variables.
- **Water Quality Portal** — discrete public water-quality site/result records from USGS, EPA, and participating monitoring partners; coastal applicability remains site- and record-specific.

Source access is represented as source-bounded query/evidence contracts. v4.13.0 does not embed private credentials in browser assets.

## Evidence classes

v4.13.0 separates eight evidence classes:

**microplastics observation · marine-litter observation · contaminant measurement · water-quality sample · biogeochemical analysis · biogeochemical forecast · non-detect · quality flag**

The initial indicator registry includes microplastics, beach/seafloor/floating litter, heavy metals, pesticides, hydrocarbons, PCBs, nutrients/eutrophication context, dissolved oxygen, pH/acidity, chlorophyll, and general water-quality samples.

## Truth boundaries

The interface is labeled:

> **EVIDENCE ORIENTATION · NOT A HEALTH OR COMPLIANCE FINDING**

The release explicitly refuses these inferences:

- no returned record does not mean clean water or no pollution;
- a source-reported non-detect is not automatically zero;
- model analysis or forecast is not an in-situ sample;
- a debris observation does not identify its source actor or transport pathway;
- a concentration value does not by itself establish ecological harm, human exposure, or health risk;
- a threshold comparison does not become a regulatory exceedance or compliance finding;
- units, matrices, methods, detection limits, qualifiers, quality flags, spatial support, and timestamps must remain explicit.

## Public contracts

```text
GET  /public/marine-pollution
GET  /public/marine-pollution/catalog
GET  /public/marine-pollution/state

POST /public/marine-pollution/measurement/normalize
POST /public/marine-pollution/debris/normalize
POST /public/marine-pollution/threshold/preview

GET  /public/marine-pollution/export-manifest
GET  /public/marine-pollution/readiness
```

## Browser environment

A deferred **Pollution & water quality** environment is loaded from the existing **Human activity & protection** environment. The base application shell therefore remains bounded rather than growing another first-load workspace.

The browser state exposes source, indicator, date, and optional point selection. Initial evidence remains unloaded until a source record is explicitly normalized or a future connector supplies a source-bounded record.

## Validation

- **1,190 automated tests passed**
- **1653 immutable distributable entries**
- **107 JavaScript files validated** across backend and WordPress asset trees
- **134 JSON/GeoJSON files parsed** in the clean source tree
- WordPress PHP syntax: **PASS**
- static security findings: **0**
- Marine Pollution direct browser gate: **PASS**
- Marine Pollution WordPress iframe gate: **PASS**
- six primary areas / 35 public routes: **preserved**
- nested `backend/backend/` runtime-state entries: **0**

Production deployment has not been performed by the build environment. The macOS installer performs deterministic package validation and then invokes the GitHub/Render promotion gate.
