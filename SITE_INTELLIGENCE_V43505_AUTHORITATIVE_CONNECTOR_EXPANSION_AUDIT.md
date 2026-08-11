# Site Intelligence v4.35.5 — Authoritative Connector Expansion III Audit

## Purpose

v4.35.5 converts a third tranche of authoritative source registrations into bounded retrieval/discovery clients. It explicitly distinguishes public LIVE retrieval from credential-gated AUTH_REQUIRED connectors and metadata-only DISCOVERY.

## Expansion III interfaces

| Connector | Authority | Mode without optional configuration | Workspace handoff | Credential |
|---|---|---|---|---|
| National Wetlands Inventory REST | U.S. Fish & Wildlife Service | LIVE | Wetlands & Inland Waters | None |
| ECHO Facility Web Services | U.S. Environmental Protection Agency | LIVE | Industrial / Water / Waste regulatory context | None |
| FIRMS Area API | NASA LANCE / FIRMS | AUTH_REQUIRED | Terrestrial Ecosystems & Wildfire | `SC_SI_NASA_FIRMS_MAP_KEY` |
| Quick Stats API | USDA National Agricultural Statistics Service | AUTH_REQUIRED | Agriculture & Food Systems | `SC_SI_USDA_NASS_API_KEY` |
| CMR GraphQL | NASA EOSDIS | DISCOVERY | Earth / Science / Space discovery | Public; optional Earthdata token |

## Retrieval controls

### USFWS NWI
- point or envelope required
- envelope capped to 5° longitude × 5° latitude
- output capped to 200 records
- GeoJSON source features retained
- inventory evidence is not a jurisdictional determination

### EPA ECHO
- all-media/CWA/RCRA service allowlist
- U.S. state, facility identifier, or bounded coordinate/radius filter required
- radius capped at 50 miles
- response-set cap applied
- source payload retained without deriving a new violation/legal/exposure judgment

### NASA FIRMS
- server-side MAP_KEY required
- official source allowlist
- area capped to 30° × 30°
- day range restricted to 1–5
- CSV fields preserved as returned
- thermal anomalies remain distinct from incident/perimeter/containment records

### USDA NASS Quick Stats
- server-side API key required
- allowlisted What/Where/When filters only
- at least one substantive commodity/sector/geography/year/aggregation filter required
- `get_counts` is called before `api_GET`; over-limit queries are rejected before retrieval
- output retains official aggregate estimate fields and suppression/source semantics

### NASA CMR GraphQL
- keyword, short name, provider, spatial, or temporal filter required
- collection result count capped
- optional Earthdata bearer token remains server-side
- CMR collection metadata remains DISCOVERY and is not treated as observation data

## Coverage change

| Measure | v4.35.4 | v4.35.5 |
|---|---:|---:|
| Source registrations | 179 | 179 |
| Machine-readable registrations | 96 | 96 |
| Implemented/discovery/config-gated | 56 | 61 |
| LIVE | 38 | 41 |
| DISCOVERY | 8 | 8 |
| REGISTERED / not retrieved | 50 | 45 |
| AUTH_REQUIRED | 10 | 12 |
| BULK | 4 | 4 |
| STALE | 0 | 0 |

The five new interfaces close five machine-readable implementation gaps. Only three existing registrations move directly to LIVE because FIRMS and NASS are correctly held at AUTH_REQUIRED until credentials are configured.

## Deployment boundary

The v4.35.3.1 hardened release contract remains authoritative: deployment verification is based on first-party release identity, runtime/application health, route structure, connector-router registration, assets, and non-blocking source-health policy. Upstream source availability is operational evidence, not a release blocker.

## Next connector priorities

The remaining machine-readable backlog is 45 registrations. Expansion IV should continue with high-authority statistical/scientific interfaces, prioritizing viable FAO/UN statistical APIs or SDMX, ILOSTAT, OECD SDMX, additional EPA data services, and authoritative geoscience/volcano services after current-interface verification.
