# Site Intelligence v4.19.0 — Terrestrial Ecosystems, Vegetation & Wildfire Intelligence

## Purpose
Extend Earth Observation from hydrology into global terrestrial-system evidence without changing the six-area / 35-route public architecture.

## Source registry
1. NASA LANCE/FIRMS — global MODIS/VIIRS active-fire detections and source-distributed burned-area products.
2. NASA EOSDIS LP DAAC / MODIS vegetation — NDVI, EVI and vegetation continuous fields.
3. Copernicus Land Cover & Forest Monitoring (LCFM) — global 10 m land-cover and tree-cover products.
4. Copernicus Global Vegetation — operational NDVI, LAI, FAPAR, FCover and burnt-area products.

## Truth boundary
**TERRESTRIAL EVIDENCE · NOT A WILDFIRE INCIDENT, SAFETY OR ECOSYSTEM-HEALTH DETERMINATION**

- Active-fire detections are thermal-anomaly/fire detections, not complete wildfire incidents, perimeters, evacuation orders or containment estimates.
- Active-fire detections are not used to estimate burned area; source burned-area products remain a separate evidence class.
- NDVI/EVI and related vegetation variables are satellite-derived proxies/estimates, not direct ecosystem-health, biomass, crop-yield or biodiversity findings.
- Land-cover classifications are not legal land use, ownership, protected status or ground-survey truth.
- Near-real-time products remain distinct from consolidated/final products.
- Empty results do not establish no fire, no vegetation stress or no land-cover change.

## Public contracts
- GET `/public/terrestrial-ecosystems`
- GET `/public/terrestrial-ecosystems/catalog`
- GET `/public/terrestrial-ecosystems/state`
- POST `/public/terrestrial-ecosystems/measurement/normalize`
- POST `/public/terrestrial-ecosystems/feature/normalize`
- POST `/public/terrestrial-ecosystems/threshold/preview`
- GET `/public/terrestrial-ecosystems/export-manifest`
- GET `/public/terrestrial-ecosystems/readiness`

## Architecture
The environment is deferred from v4.18 Hydrology and remains inside Earth Observation. Primary area count delta: 0. Public route count delta: 0.
