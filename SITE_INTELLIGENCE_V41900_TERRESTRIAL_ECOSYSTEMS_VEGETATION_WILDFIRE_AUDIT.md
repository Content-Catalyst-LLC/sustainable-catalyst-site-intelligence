# Site Intelligence v4.19.0 — Terrestrial Ecosystems, Vegetation & Wildfire Audit

## Release contract
- Version: 4.19.0
- Contract: `terrestrial-ecosystems-vegetation-wildfire-intelligence`
- Route area: `earth`
- Source families: 4
- Primary-area delta: 0
- Public-route delta: 0

## Evidence classes
- near-real-time fire detection
- satellite burned area
- satellite vegetation index
- satellite fractional cover
- satellite land cover
- satellite tree cover
- satellite change classification
- near-real-time vegetation
- consolidated vegetation

## Required false inferences
The platform does not infer a wildfire incident from a satellite fire detection; burned area from active-fire counts; current active fire from a burned-area classification; ecosystem health from NDVI/EVI alone; legal land use from land-cover classes; ground truth from a satellite classification; or a safety warning from a threshold comparison.

## Source and product maturity
Source URL, evidence class, observation date, product maturity, quality status, spatial query context, limitations and source-specific semantics remain visible in normalized records and export manifests.
