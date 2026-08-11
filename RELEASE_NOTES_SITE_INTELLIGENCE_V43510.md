# Site Intelligence v4.35.11 — Authoritative Connector Expansion IV

v4.35.11 continues the authoritative-data closure branch with five first-party machine interfaces: FAOSTAT, ILOSTAT SDMX, OECD Data Explorer SDMX, EPA Facility Registry Service, and USGS Volcano Hazards Program HANS. The release preserves bounded retrieval, semantic/provenance boundaries, and non-blocking upstream health.

## Connector expansion
- FAOSTAT data API: LIVE implementation with server-configurable base URL.
- ILOSTAT SDMX / indicator service: LIVE.
- OECD Data Explorer SDMX API: LIVE.
- EPA Facility Registry Service public API: LIVE.
- USGS Volcano HANS: LIVE; closes the pre-existing volcano machine-readable gap.

## Production audit after expansion
- 188 total source registrations across 44 source-bearing workspaces.
- 105 machine-readable registrations.
- 41 machine-readable LIVE registrations and 6 DISCOVERY registrations.
- 11 machine-readable AUTH_REQUIRED registrations.
- 43 machine-readable REGISTERED integrations still awaiting retrieval.
- 4 machine-readable BULK-only registrations.
- 0 known stale implemented connectors.

The public authoritative connector catalog now exposes 25 interfaces: 21 LIVE, 2 DISCOVERY, and 2 AUTH_REQUIRED.
