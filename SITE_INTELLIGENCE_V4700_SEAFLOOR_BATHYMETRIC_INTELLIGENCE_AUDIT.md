# Site Intelligence v4.14.0 — Seafloor & Bathymetric Intelligence Audit

## Architecture

The release preserves the v4 public route architecture. Seafloor Intelligence is a deferred Earth Observation sub-environment reached from Water Column & Depth Explorer. It does not add a top-level navigation route.

Observation sequence:

`Earth / Orbit → Ocean Surface → Water Column → Seafloor`

## Source registry

### GEBCO_2026

Registered as the global terrain backbone. The contract exposes GEBCO grid/download and WMS discovery but distinguishes a gridded cell from an individual sounding. The source-resolution field is preserved rather than converted into an accuracy statement.

### EMODnet Bathymetry

Registered as a harmonised regional DTM and survey/source-discovery pathway for European sea regions. The contract preserves the distinction between the harmonised terrain surface and heterogeneous contributing surveys.

### NOAA NCEI Bathymetry & Seafloor Mapping

Registered for survey/archive evidence including multibeam, singlebeam, lidar, crowdsourced bathymetry, DEMs, and catalog footprints. A catalog footprint remains a footprint; it is never treated as verified depth at every enclosed point.

## Evidence classes

The release keeps these categories separate:

- global gridded bathymetry
- regional DTM
- multibeam survey
- singlebeam survey
- lidar bathymetry
- crowdsourced bathymetry
- digital elevation model
- survey footprint
- source-type grid
- rendered map service

## Non-fabrication gates

The public state begins with no terrain value, no point-level coverage claim, no individual-sounding claim, and no inferred vertical datum. The interface does not silently flip negative elevation into positive depth. No datum conversion is performed without an explicit method. Hillshade is not a measurement.

## Browser contract

The direct and iframe browser test enters the Seafloor panel from Water Column, selects NOAA NCEI multibeam coverage, changes geographic/date state, and verifies that the interface still reports the terrain value and point coverage as not loaded/not verified.

## Deployment gate

The live promotion script independently fetches the Seafloor overview, catalog, bounded default state, readiness response, and shipped `seafloor-bathymetry-v4700.js` asset. Deployment cannot report success unless the non-fabrication readiness checks remain true.
