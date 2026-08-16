# Site Intelligence v4.36.1 — Ocean & Space Live Evidence Rendering, Connector Binding & OpenAPI Recovery

## Release purpose

v4.36.1 closes the gap between Site Intelligence's already-working authoritative connector layer and the public Ocean/Space workspaces. The release does not weaken the v4.36.0 R3 Science/Ocean hydration contract, alter the six-area / 35-route architecture, or turn source discovery into fabricated measurements. It carries verified provider records through to the browser while preserving explicit source, coverage, uncertainty, and interpretation boundaries.

## Ocean live evidence rendering

- **Ocean Surface** now calls the existing NOAA CoastWatch ERDDAP connector and renders bounded dataset-discovery records for the selected surface variable. Dataset discovery is not presented as a point measurement; exact point/time coverage remains dataset-specific.
- **Marine Biodiversity** now calls the existing IOC-UNESCO OBIS connector and renders bounded occurrence records with scientific name, event date, coordinates, basis of record, and dataset identity where supplied by OBIS. Zero results never become an absence claim.
- **Coastal Change** now calls the existing NOAA CO-OPS connector and renders station water-level records while retaining station, datum, product, units, time-zone, quality/flag, and observation-versus-prediction boundaries.
- Provider failures are rendered as explicit unavailable states. No fallback value, zero, nearest sample, substitute source, or silent model estimate is fabricated.

## Space live evidence rendering

- **Exoplanets & Atmospheres** now calls NASA Exoplanet Archive TAP through the existing Site Intelligence connector and renders published planetary-system records directly in the workspace, including discovery method/year, orbital period, radius, mass, equilibrium temperature, and system distance when present.
- **Lunar & Planetary Intelligence** now calls NASA EOSDIS CMR through the existing discovery connector and renders bounded collection metadata for Moon/Mars discovery context.
- **Orbital Earth** retains the existing real NASA EOSDIS GIBS imagery path and its explicit no-fabricated-ephemeris/no-fabricated-swath boundaries.
- Astronomy, planetary, exoplanet, and solar-system interpretation boundaries remain conservative: metadata is not observation value, equilibrium temperature is not surface temperature, and no parameter becomes a habitability or life-detection finding.

## OpenAPI recovery

Production `/openapi.json` previously failed because two administrative request bodies used the unresolved annotation `Dict[str, Any]` while `Dict` was not imported. FastAPI/Pydantic therefore encountered an unresolved `ForwardRef` while building the schema.

v4.36.1 replaces those annotations with native `dict[str, Any]` and adds an explicit regression test that generates the complete FastAPI OpenAPI schema and requests `/openapi.json` through `TestClient`.

## Validation

- 1,684 deterministic pytest tests passed across five bounded chunks.
- FastAPI OpenAPI generation succeeds with 1,323 registered paths in the validated artifact environment.
- Changed JavaScript assets pass `node --check` and remain byte-identical between the backend public app and WordPress plugin copies.
- PHP plugin syntax remains valid.
- A deterministic Playwright browser gate is included for Ocean Surface, OBIS biodiversity, NOAA CO-OPS coastal evidence, NASA Exoplanets, and NASA CMR. The browser gate intercepts external provider calls with bounded fixtures so release certification remains network-independent.

## Release boundary

External provider availability remains operational evidence and is not a release prerequisite. Live source records are rendered when available; missing or unavailable provider data remains visibly missing/unavailable. Platform Core integration remains optional for local Ocean/Space workspace availability and remains separately governed by the established Core integration contract.

## Browser certification

A deterministic Playwright gate executes the shipped Ocean Surface, Marine Biodiversity, Coastal Change, Exoplanet, and Planetary browser modules against first-party catalog/state contracts plus bounded NOAA/OBIS/NASA fixtures. The gate validates browser rendering without making upstream provider availability a release blocker.
