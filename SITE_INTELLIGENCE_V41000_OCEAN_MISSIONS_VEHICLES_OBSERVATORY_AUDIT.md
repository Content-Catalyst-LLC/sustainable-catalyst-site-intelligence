# Site Intelligence v4.12.0 — Ocean Missions, Vehicles & Observatory Network Audit

## Architecture

The module remains inside the existing Earth Observation/ocean chain and creates no new top-level public workspace. It extends Marine Biodiversity with a deferred `Missions & network` interface.

## Registered source contracts

- **Argo / Argovis** — profiling floats, cycles, trajectories, profiles, and source-reported positions.
- **U.S. IOOS** — gliders, buoys, moorings, and fixed observing stations across regional systems.
- **Ocean Networks Canada Oceans 3.0** — fixed observatories, cameras, hydrophones, mobile platforms, ROV/AUV and deployment metadata where published.
- **NOAA Ocean Exploration / NCEI archives** — research vessels, expeditions, ROV/AUV dives, navigation and historical mission records.

## Evidence boundaries

The normalized contract keeps registry identity, platform class, mission identity, status, timestamped position, and track points separate. A normalized record is source-attributed and is not independently network-verified. No source record is automatically promoted to a live operational feed.

The track contract stores only source-supplied points. It performs no interpolation, does not claim a continuous path between points, does not treat the last point as a current position, and does not project a future trajectory.

## Public APIs

- `GET /public/ocean-missions`
- `GET /public/ocean-missions/catalog`
- `GET /public/ocean-missions/state`
- `POST /public/ocean-missions/platform/normalize`
- `POST /public/ocean-missions/mission/normalize`
- `POST /public/ocean-missions/track/normalize`
- `GET /public/ocean-missions/export-manifest`
- `GET /public/ocean-missions/readiness`
