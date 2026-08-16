# Site Intelligence v4.38.0 — Live Underwater Media Discovery, Imagery & Video Retrieval

## Release purpose

v4.38.0 completes the first live acquisition layer for Underwater Observation. The previous workspace could describe ONC, FathomNet and NOAA source boundaries but did not execute media discovery. This release makes underwater imagery/video a source-backed public workflow while preserving missing-data and evidence-class boundaries.

## Live provider lanes

- **FathomNet** — default public underwater image and annotation discovery. No Site Intelligence credential is required.
- **NOAA Ocean Exploration / NCEI** — public expedition, dive, still-image, video and archive discovery. No Site Intelligence credential is required.
- **Ocean Networks Canada Oceans 3.0 / SeaTube** — optional token-authenticated camera/archive discovery. Configure `SC_SI_ONC_API_TOKEN` to enable this lane. Its absence is explicitly non-blocking.

Provider failures remain isolated. Site Intelligence does not substitute another provider's media, invent a nearest observation, or convert a missing image into an orientation illustration presented as evidence.

## Public API

- `GET /public/underwater-media/providers`
- `GET /public/underwater-media/readiness`
- `POST /public/underwater-media/search`
- `GET /public/underwater-media/onc/file?filename=...` for bounded server-side ONC still-image delivery

The ONC token remains server-side and is redacted from public provenance. The proxy rejects path traversal and non-image file requests.

## Browser experience

Underwater Observation now opens on FathomNet rather than a fake `0,0 / 0 m` query. Users can search by provider-appropriate dimensions, inspect candidate media cards, open still imagery/video when supplied, and review record ID, provider, coordinates, depth, observation time, annotations, credit, rights and truth boundaries. Fields remain blank when the provider did not supply them.

## Inherited platform guarantees

- Ocean remains a first-class featured system with 11 marine systems.
- Space remains a first-class featured system with six local Space workspaces.
- Platform Core remains optional for local Ocean/Space discovery.
- The six-area / 35-route public architecture is unchanged.
- Country identity, Palestine/Israel routing, country evidence hierarchy, production-soak and evidence-truth gates remain inherited.

## Release gate

Readiness is network-free. FathomNet and NOAA provider lanes must be registered as public, the ONC missing-credential state must remain non-blocking, and the live Underwater control plane must be inherited by Ocean readiness. Live upstream availability is operational evidence and does not determine release validity.
