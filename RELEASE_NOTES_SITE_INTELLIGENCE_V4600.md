# Site Intelligence v4.8.0 — Water Column & Depth Explorer

## Purpose

Extend Global Ocean Intelligence below the sea surface without converting a depth request into a fabricated observation. v4.8.0 adds a source-bounded vertical navigation and profile-evidence contract inside the existing Earth Observation route.

## Source architecture

The release registers three complementary pathways:

- **Argo profiles via Argovis** — public profile/platform/API discovery for Argo physical and BGC profile data. Site Intelligence treats Argo as source-reported in-situ profile samples with retained depth/pressure and QC context.
- **Copernicus Marine** — dataset-specific 3-D analysis, forecast, reanalysis, and model depth levels through the current Copernicus Marine Toolbox/data services. Gridded depth fields are never relabeled as in-situ observations.
- **Ocean Networks Canada Oceans 3.0** — deployment, device, cast, fixed-observatory, mobile-platform, and data-product discovery. A fixed sensor depth is not silently interpreted as a full water-column profile.

Upstream credentials/tokens are never embedded in public state, browser assets, manifests, or fixtures.

## New public contracts

- `GET /public/water-column`
- `GET /public/water-column/catalog`
- `GET /public/water-column/state`
- `POST /public/water-column/profile/normalize`
- `POST /public/water-column/depth/resolve`
- `GET /public/water-column/export-manifest`
- `GET /public/water-column/readiness`

## Evidence rules

- Selecting a depth is a navigation request, not proof of a source record at that depth.
- v4.8.0 performs **no interpolation** between profile samples.
- The nearest available sample may be disclosed as context but is never substituted as the requested-depth value.
- Pressure and geometric depth are not silently converted into one another.
- Quality flags remain attached to source samples rather than being collapsed into a generic pass/fail score.
- In-situ profile, fixed observatory, mobile platform, model, analysis, forecast, and reanalysis evidence remain distinct.
- Missing samples remain missing.

## Interface

The deferred Water Column panel adds variable/source/date/location controls and a 0–11,000 m interactive depth rail, matching the API navigation bound. The local water-column graphic is an orientation field and explicitly says `NO PROFILE SAMPLE RENDERED`; it does not draw fake temperature, oxygen, salinity, or biological conditions.

## Compatibility

No new top-level route is introduced. The v4 architecture remains six primary navigation areas and 35 public routes. Global Ocean Intelligence v4.5, Orbital Earth, Lunar & Planetary Intelligence, Astronomical Observation, Solar System Navigation, Data Truth, record provenance, production soak, service-worker closure, and WordPress fixed-viewport behavior remain preserved.
