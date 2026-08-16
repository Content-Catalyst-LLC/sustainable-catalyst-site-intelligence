# Site Intelligence v4.38.0 — Live Underwater Media Audit

## Architecture

The release adds `backend/app/live_underwater_media_v4370.py` as an independent provider-control plane. It normalizes source records into a bounded public media-record contract while retaining provider identity and source-specific metadata.

### FathomNet

The default lane uses FathomNet's public image API. Concept searches use the provider concept-query path; an empty query uses the bounded image-list path. Only records with a valid HTTP(S) media URL are promoted to candidate media. Annotation labels remain annotations, not abundance findings or locally verified species determinations.

### NOAA Ocean Exploration / NCEI

NOAA discovery supports expedition/dive context and source handoff to the Ocean Exploration Video Portal. When an expedition identifier is supplied, the connector can inspect the NCEI Okeanos expedition archive for bounded still-image, video and media-package links. Generic portal search remains a source handoff rather than an invented local search result.

### Ocean Networks Canada Oceans 3.0

ONC is credentialed with `SC_SI_ONC_API_TOKEN`. Discovery is performed server-side. Candidate still images use a Site Intelligence proxy endpoint so the API token is never exposed in browser URLs. Video/archive records remain source handoffs when direct delivery would require credential-bearing URLs. Missing ONC credentials do not block the two public lanes.

## Truth boundaries

- A media candidate is a source-attributed record, not a locally fabricated observation.
- Missing point/depth/time metadata stays missing.
- No default `0,0` coordinate or `0 m` depth is treated as an observation.
- Nearby sensors are not assumed synchronized with a camera record.
- FathomNet annotations are not silently promoted to verified taxonomic or abundance conclusions.
- NOAA expedition presence does not imply continuous visual coverage.
- ONC authentication state does not determine FathomNet/NOAA availability.
- Asset-specific rights/citation requirements must be checked before reuse.

## Release integration

`underwater_observation_v4800.py` now inherits the live-media readiness contract, and `ocean_observation_marine_systems_v4360.py` inherits that Underwater readiness as one of the 11 Ocean systems. Production deployment verification requires the three-lane control plane but explicitly does not require the ONC token.

## Browser certification

The v4.37 browser gate uses deterministic provider fixtures and verifies: FathomNet defaults, all three provider choices are visible, candidate cards render, an actual media element is selected, unset query dimensions remain blank, ONC is marked token-required, and no browser errors occur.
