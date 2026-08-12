# Site Intelligence v4.35.13 — High-Priority Workspace Connector Closure III: Water, Hydrology & Sanitation

v4.35.13 continues the workspace-by-workspace “simply works” closure program by eliminating ambiguous REGISTERED machine-interface gaps in Hydrology, Rivers, Flood & Drought and Water, Wastewater & Sanitation.

## Added
- EPA SDWIS / Envirofacts bounded public drinking-water system retrieval.
- Bounded OpenStreetMap / Overpass water-infrastructure retrieval.
- NOAA/NIDIS Drought.gov public JSON/GeoJSON/TopoJSON retrieval.
- NASA GPM / IMERG collection discovery through NASA CMR.
- Copernicus GloFAS public product/layer discovery.
- Hydrology and Water/Sanitation closure accounting in the production audit and closure ledger.
- Ten public API/workspace routes for the five interfaces above.

## Evidence semantics
- EPA SDWIS administrative/regulatory records are not real-time tap-water telemetry or a new Site Intelligence safety/compliance determination.
- OpenStreetMap water infrastructure is supplemental community-mapped evidence and does not prove operational status, capacity, ownership, water quality, or service territory.
- NIDIS/Drought.gov source-defined drought products remain source-defined; Site Intelligence does not issue independent drought declarations or emergency determinations.
- NASA GPM / IMERG catalogue records are discovery metadata, not precipitation observations; satellite precipitation estimates remain distinct from rain gauges.
- GloFAS layer availability is discovery of modeled hydrological/flood products, not a local gauge observation or Site Intelligence-issued flood warning.
- WHO/UNICEF JMP remains a non-machine portal/source in the current audit until a stable authoritative machine interface is independently verified.
- Missing or unavailable values remain missing.
- External upstream health remains non-blocking for deployment.

## Coverage
Machine-readable registrations: 108; LIVE: 46; DISCOVERY: 12; AUTH_REQUIRED: 14; REGISTERED/not retrieved: 34; BULK: 2; STALE: 0.

Public connector catalogue: 40 interfaces — 26 LIVE, 8 DISCOVERY, 6 AUTH_REQUIRED.

Hydrology REGISTERED backlog: 0. Water/Wastewater/Sanitation REGISTERED backlog: 0.

## Validation
Complete deterministic suite: 1,539 tests. Release-specific regressions: 12. Final manifest/static/security/browser results are recorded in `SITE_INTELLIGENCE_V43513_BUILD_VALIDATION.txt`.
