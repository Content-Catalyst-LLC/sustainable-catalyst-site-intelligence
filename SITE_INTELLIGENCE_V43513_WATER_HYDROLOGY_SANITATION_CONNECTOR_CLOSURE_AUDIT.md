# Site Intelligence v4.35.13 — Water, Hydrology & Sanitation Connector Closure Audit

## Purpose
Close ambiguous machine-interface gaps in the Hydrology, Rivers, Flood & Drought and Water, Wastewater & Sanitation workspaces without overstating regulatory records, community mapping, satellite estimates, model products, or discovery metadata.

## Hydrology closure
- USGS Water Data OGC remains a LIVE first-party bounded water-observation path.
- NOAA/NIDIS Drought.gov public JSON/GeoJSON/TopoJSON is implemented as LIVE bounded retrieval.
- NASA GPM / IMERG is represented through NASA CMR as DISCOVERY; metadata discovery is not precipitation observation retrieval.
- Copernicus GloFAS public product/layer availability is represented as DISCOVERY; model-product discovery is not a local gauge observation or platform-issued flood warning.
- Hydrology REGISTERED machine-interface backlog: 0.
- Hydrology has a credential-free LIVE path.

## Water / Wastewater / Sanitation closure
- OpenStreetMap / Overpass water infrastructure is implemented as bounded LIVE supplemental retrieval.
- EPA ECHO wastewater remains a LIVE regulatory/facility path.
- EPA SDWIS / Envirofacts is implemented as LIVE bounded public drinking-water system/regulatory retrieval.
- WHO/UNICEF JMP remains a non-machine portal/source in the current audit; no unverified API endpoint is invented.
- Water/Wastewater/Sanitation REGISTERED machine-interface backlog: 0.
- Water/Wastewater/Sanitation has credential-free LIVE paths.

## Machine-readable production audit
- Registrations: 108
- LIVE: 46
- DISCOVERY: 12
- AUTH_REQUIRED: 14
- REGISTERED, not retrieved: 34
- BULK: 2
- STALE: 0
- Implemented / discovery / configuration-gated: 72

## Public connector catalogue
- Interfaces: 40
- LIVE: 26
- DISCOVERY: 8
- AUTH_REQUIRED: 6

## Deployment boundary
Connector/readiness and production-readiness checks are deterministic and make no upstream calls. External provider availability is operational source health and is non-blocking for release promotion.
