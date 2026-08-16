# Site Intelligence v4.36.1 — Live Evidence Rendering & OpenAPI Audit

## Production diagnosis carried into the build

The v4.36.0 production service had already proved that NOAA ERDDAP, NOAA CO-OPS, IOC-UNESCO OBIS, NASA Exoplanet Archive TAP, and NASA CMR could return successful live responses through Site Intelligence. Platform Core was also connected in both directions. The remaining defect was therefore not provider reachability or Core configuration: browser workspaces were still rendering query plans/orientation states instead of carrying those connector records into the user-facing evidence surface.

## Browser binding repairs

| Workspace | Existing authoritative connector | v4.36.1 browser behavior |
|---|---|---|
| Ocean Surface | NOAA CoastWatch ERDDAP | Live bounded dataset-discovery records rendered in-workspace |
| Marine Biodiversity | IOC-UNESCO OBIS API v3 | Live occurrence records rendered with source fields |
| Coastal Change | NOAA CO-OPS Data API | Live station water-level records rendered with metadata/flags |
| Exoplanets & Atmospheres | NASA Exoplanet Archive TAP | Live published planetary-system records rendered |
| Lunar & Planetary Intelligence | NASA EOSDIS CMR | Live collection metadata rendered as discovery evidence |
| Orbital Earth | NASA EOSDIS GIBS | Existing real imagery retained |

## Truth boundaries retained

1. ERDDAP dataset discovery does not establish a measurement at a selected point/time.
2. OBIS occurrence records do not establish abundance, complete coverage, current occupancy, or absence outside returned evidence.
3. NOAA CO-OPS station observations are station-, datum-, product-, units-, and time-zone-specific; predictions are not observations.
4. NASA CMR collection metadata is discovery evidence, not a planetary observation value or image.
5. NASA Exoplanet Archive equilibrium temperature is not surface temperature and is not a habitability finding.
6. Provider errors remain provider errors. The browser does not invent replacements.

## OpenAPI root cause and repair

`backend/app/main.py` contained two request-body annotations using `Dict[str, Any]` while only `Any`, `Mapping`, and `Optional` were imported from `typing`. With postponed annotations enabled, Pydantic received an unresolved `ForwardRef('Dict[str, Any]')` and `/openapi.json` failed while generating definitions.

Repair: both annotations now use native `dict[str, Any]`, eliminating the unresolved forward reference without introducing a compatibility alias.

## Regression controls

- `backend/tests/test_ocean_space_live_evidence_openapi_v4361.py` validates release identity, complete OpenAPI generation, `/openapi.json`, connector-route presence, live browser bindings, evidence-boundary copy, and WordPress/backend asset parity.
- `scripts/browser_live_evidence_v4361.py` validates deterministic browser rendering with bounded provider fixtures.
- Existing v4.36.0 R3 Ocean hydration, Science discovery, country integrity, evidence presentation, Core integration, and connector tests remain inherited.
