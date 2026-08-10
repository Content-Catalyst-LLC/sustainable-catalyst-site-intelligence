# Site Intelligence v4.13.0 — Underwater Observation & Visual Evidence

v4.13.0 extends the existing Earth Observation chain from seafloor terrain into source-attributed underwater visual observations without adding a new top-level route.

Observation sequence:

`Orbit → Surface → Ocean Surface → Water Column → Seafloor → Underwater Observation`

## New capability

- Registers Ocean Networks Canada Oceans 3.0 / SeaTube, FathomNet, and NOAA Ocean Exploration / NCEI as bounded underwater-visual evidence sources.
- Adds still-image, video-segment, video-stream, and live-camera-reference media classes.
- Adds source-attributed media normalization with point, depth, time, station, dive, expedition, credit, rights statement, and immutable SHA-256 fingerprint fields.
- Adds visual annotation normalization for expert-human, human, citizen-science, and model-inference labels with optional bounding boxes and confidence.
- Adds a deferred Underwater Observation panel after Seafloor & Bathymetric Intelligence so the initial application shell is not enlarged for users who never enter the ocean workflow.
- Adds evidence-manifest export and public readiness contracts.

## Scientific and rights boundaries

- The local underwater scene is orientation-only and is not represented as a photograph or video frame.
- A camera, station, expedition, dive, or catalog listing does not prove media exists at a requested point, depth, or time.
- No visual record is fabricated when source media is absent.
- Model inference is never promoted to a verified biological observation.
- An annotation or bounding box does not establish abundance, population size, or ecosystem condition beyond the source record.
- Nearby environmental-sensor values are not assumed synchronized or co-located with visual media.
- Rights, licenses, credits, and attribution remain source/asset-specific. NOAA Ocean Exploration Video Portal video may carry a public-domain source statement; that statement is not generalized to unrelated assets.

## Public contracts

- `GET /public/underwater-observation`
- `GET /public/underwater-observation/catalog`
- `GET /public/underwater-observation/state`
- `POST /public/underwater-observation/media/normalize`
- `POST /public/underwater-observation/annotation/normalize`
- `GET /public/underwater-observation/export-manifest`
- `GET /public/underwater-observation/readiness`

## Compatibility

The v4 platform remains six primary areas and 35 public routes. Underwater Observation extends the existing `earth` route. Existing Orbital Earth, Lunar & Planetary, Astronomical Observation, Solar System, Ocean Surface, Water Column, Seafloor, Data Truth, provenance, publication, monitoring, governance, and WordPress embed contracts remain compatible.
