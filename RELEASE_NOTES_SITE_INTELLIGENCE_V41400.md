# Site Intelligence v4.15.0 — Coastal Change, Sea Level & Blue-Carbon Intelligence

## Release purpose

v4.15.0 extends the existing Earth Observation ocean continuum to the dynamic coastal interface without adding a new primary application area or public navigation route. The release keeps water-level observations, tide predictions, sea-level-rise screening scenarios, shoreline analyses, coastal land-cover evidence, wetlands, and mangroves as distinct source-bounded evidence classes.

## Registered source families

1. **NOAA CO-OPS Tides & Currents** — station observations, tide predictions, station metadata, vertical-datum context, and related derived coastal water-level products.
2. **NOAA Digital Coast / Sea Level Rise** — screening-level sea-level-rise inundation, mapping confidence, coastal land cover, tidal wetland, and wetland-migration planning data.
3. **USGS Coastal Change Hazards Portal** — machine-readable observed shoreline change, storm scenarios, future shoreline change, and future coastal-hazard products.
4. **Global Mangrove Watch** — global remote-sensing evidence for mangrove extent and change, retained as habitat evidence unless separate source material explicitly supports a carbon quantity or project claim.

## New public contracts

- `GET /public/coastal-change`
- `GET /public/coastal-change/catalog`
- `GET /public/coastal-change/state`
- `POST /public/coastal-change/water-level/normalize`
- `POST /public/coastal-change/shoreline/normalize`
- `POST /public/coastal-change/habitat/normalize`
- `POST /public/coastal-change/scenario/preview`
- `GET /public/coastal-change/export-manifest`
- `GET /public/coastal-change/readiness`

## Data-truth boundaries

- A tide prediction is not an observed water level and is not silently upgraded into a total-water-level forecast.
- A sea-level-rise inundation layer is screening-level planning evidence, not an exact parcel flood boundary, navigational product, permitting determination, or evacuation instruction.
- A shoreline-change rate or projection does not guarantee a future shoreline position, property loss, or safety outcome.
- Vertical datum, source timestamp, unit, method, uncertainty, spatial resolution, scenario height, and product identity remain explicit when records are normalized.
- A wetland or mangrove map is habitat evidence. Site Intelligence does not derive carbon stock, sequestration rate, restoration success, additionality, permanence, avoided emissions, or carbon-credit eligibility from habitat presence alone.
- Empty results remain empty results; they do not establish absence of flooding, erosion, change, wetland, mangrove, or risk.

## Interface

The new deferred coastal panel follows Marine Pollution inside the existing ocean sequence and is labeled:

**SCREENING & EVIDENCE ORIENTATION · NOT A PARCEL FORECAST OR CARBON CLAIM**

The browser surface offers source, indicator, date, and geographic query state, an explicit Data Truth panel, source opening, and a reviewable evidence-manifest export.

## Architecture

- Primary areas: **6**
- Public navigation routes: **35**
- New top-level route count: **0**
- WordPress embed model: unchanged
- Runtime-state exclusion under `backend/backend/`: preserved
- Service-worker automatic reload policy: unchanged

## Production deployment

The package is prepared for the existing resume-safe GitHub and Render promotion workflow. Production promotion is not performed by the build environment. Install the WordPress ZIP only after the installer verifies the exact v4.15.0 release id, Git commit, Render backend version, and live release gate.
