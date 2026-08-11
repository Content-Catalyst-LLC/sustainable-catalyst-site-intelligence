# Site Intelligence v4.35.2 — Authoritative API / Workspace Audit Snapshot

**Audit date:** 2026-08-10

This snapshot is generated from the shipped repository registries and implemented-client map. It does not make upstream network calls and therefore measures repository integration coverage, not current provider uptime.

## Summary

- Source registrations: **179**
- Unique endpoints/records: **135**
- Source-bearing workspaces/inventories: **39**
- Machine-readable registrations: **96**
- Implemented/discovery/configuration-gated registrations: **25**

| Class | Registrations |
|---|---:|
| LIVE | 16 |
| DISCOVERY | 1 |
| REGISTERED | 70 |
| AUTH_REQUIRED | 8 |
| BULK | 4 |
| STALE | 0 |
| UNAVAILABLE | 80 |

## Priority connector targets

- **Hydrology, Rivers, Flood & Drought** — `usgs-water-ogc-v0` → LIVE: Workspace already registers USGS Water Data but does not retrieve observations.
- **Ocean Surface** — `noaa-coastwatch-erddap` → LIVE: Workspace already prepares ERDDAP query plans; execute constrained dataset/point/time retrievals next.
- **Exoplanets, Habitability & Biosignatures** — `nasa-exoplanet-tap` → LIVE: Use the official TAP/ADQL service instead of registry-only planet query plans.
- **Humanitarian / future Migration & Displacement** — `unhcr-refugee-statistics-v1` → LIVE: Direct authoritative displacement statistics with country/year/demographic dimensions and footnotes.
- **Earth / Science / Space discovery** — `nasa-cmr-search` → DISCOVERY: Use CMR as a discovery backbone so NASA dataset availability is searched rather than hard-coded one product at a time.

## Workspace matrix

| Workspace | Registrations | Machine-readable | Connector gap |
|---|---:|---:|---:|
| Agriculture, Crops & Food Systems | 4 | 1 | 1 |
| Atmosphere, Air Quality & Aerosols | 4 | 3 | 3 |
| Biodiversity & Conservation | 4 | 4 | 3 |
| Climate Baselines, Anomalies & Extremes | 4 | 2 | 2 |
| Coastal Change, Sea Level & Blue Carbon | 4 | 1 | 1 |
| Conflict & Human Security | 6 | 0 | 0 |
| Cryosphere | 4 | 3 | 3 |
| Digital Connectivity | 4 | 4 | 3 |
| Energy Infrastructure & Power Systems | 4 | 4 | 4 |
| Exoplanets, Habitability & Biosignatures | 4 | 4 | 4 |
| Geosphere, Earthquakes & Volcanoes | 4 | 1 | 1 |
| Human Development | 9 | 0 | 0 |
| Human Settlements & Built Environment | 4 | 3 | 2 |
| Humanitarian Intelligence | 5 | 4 | 4 |
| Hydrology, Rivers, Flood & Drought | 4 | 2 | 2 |
| Industrial Manufacturing & Trade | 4 | 4 | 2 |
| International Law & Governance | 10 | 0 | 0 |
| Legacy Live External Connectors | 9 | 8 | 3 |
| Marine Biodiversity & Bioacoustics | 4 | 3 | 3 |
| Marine Human Activity & Protected Areas | 4 | 2 | 2 |
| Marine Pollution & Water Quality | 4 | 2 | 2 |
| Mining & Critical Materials | 4 | 3 | 3 |
| Ocean Events & Hazards | 4 | 1 | 1 |
| Ocean Governance & Maritime Boundaries | 4 | 1 | 1 |
| Ocean Missions & Observatory Networks | 4 | 1 | 1 |
| Ocean Surface | 3 | 3 | 3 |
| SETI & Technosignatures | 4 | 3 | 3 |
| Seafloor & Bathymetry | 3 | 3 | 3 |
| Soils & Land Degradation | 4 | 2 | 2 |
| Solid Waste & Circular Materials | 4 | 4 | 3 |
| Sources & Methodology | 8 | 7 | 4 |
| Sustainable Development Connectors | 9 | 0 | 0 |
| Terrestrial Ecosystems & Wildfire | 4 | 1 | 1 |
| Transportation Infrastructure | 4 | 1 | 1 |
| Underwater Observation & Visual Evidence | 3 | 2 | 2 |
| Unified Live Events | 3 | 1 | 1 |
| Water Column & Depth | 3 | 3 | 3 |
| Water, Wastewater & Sanitation | 4 | 3 | 3 |
| Wetlands & Inland Waters | 4 | 2 | 2 |
