# Site Intelligence v4.27.0 — Global Transportation Networks, Ports, Airports & Transit Intelligence

## Purpose

v4.27.0 extends the Earth Observation evidence chain from Human Settlements into transportation networks and mobility infrastructure while preserving the six-primary-area / 35-public-route architecture.

## Registered source families

1. **Overture Maps Transportation** — global road, rail and water transportation segments/connectors. The source remains mapping/network evidence and is never silently promoted into a guaranteed navigable, legally accessible, current or safe route.
2. **UNECE UN/LOCODE** — coded trade and transport locations, including port, airport, rail-terminal and road-terminal functions. A listed code/function does not establish current operating status, capacity or availability.
3. **OurAirports** — public-domain community-maintained airport, runway and navaid data. These records are not official aeronautical information and are not suitable for navigation, NOTAM, runway-operability or safety determinations.
4. **MobilityData Mobility Database** — global discovery catalog for GTFS Schedule, GTFS Realtime and GBFS feeds. Catalog/feed presence does not guarantee current service, arrival times, accessibility, fares, completeness or producer-data accuracy.

## Public contracts

- `GET /public/transportation-infrastructure`
- `GET /public/transportation-infrastructure/catalog`
- `GET /public/transportation-infrastructure/state`
- `POST /public/transportation-infrastructure/feature/normalize`
- `POST /public/transportation-infrastructure/feed/normalize`
- `POST /public/transportation-infrastructure/accessibility/preview`
- `GET /public/transportation-infrastructure/export-manifest`
- `GET /public/transportation-infrastructure/readiness`

## Truth boundary

**TRANSPORTATION EVIDENCE · NOT NAVIGATION, OPERATING STATUS OR SAFETY DETERMINATION**

The platform does not infer route operability, legal access, facility operating status, infrastructure capacity, official aeronautical status, current transit service, complete transit coverage, emergency access, safety or navigation instructions from these evidence families.

## Architecture

- Six primary public areas preserved.
- 35 public routes preserved.
- Transportation is deferred from the Human Settlements Earth Observation surface.
- Backend and WordPress browser assets are byte-mirrored.
- Existing runtime-state isolation and `backend/backend/` exclusion remain mandatory.
- The bounded Render verifier now includes a transportation deep gate.
