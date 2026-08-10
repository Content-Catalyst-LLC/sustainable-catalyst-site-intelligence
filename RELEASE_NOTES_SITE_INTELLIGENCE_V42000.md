# Site Intelligence v4.20.0 — Global Geosphere, Earthquake & Volcano Intelligence

Site Intelligence v4.20.0 extends the Earth Observation sequence into solid-Earth evidence while preserving the six-primary-area / 35-public-route architecture.

## New evidence environment

The release adds a deferred **Geosphere, Earthquake & Volcano Intelligence** environment after Terrestrial Ecosystems. It registers four complementary source families:

1. **USGS Earthquake Catalog & Real-time Feeds** — FDSN event queries, preferred event metadata, review status, magnitude/depth and real-time GeoJSON orientation.
2. **USGS ShakeMap & PAGER** — event-linked shaking and impact-estimation products kept separate from direct structural-damage or confirmed-loss evidence.
3. **USGS Volcano Hazards Program HANS** — source-issued volcano activity notices, alert levels, aviation color codes and status messages.
4. **NASA/JPL ARIA** — InSAR/rapid-response ground-deformation evidence with geometry, coherence and preliminary-product caveats retained.

## New public contracts

- `GET /public/geosphere`
- `GET /public/geosphere/catalog`
- `GET /public/geosphere/state`
- `POST /public/geosphere/measurement/normalize`
- `POST /public/geosphere/notice/normalize`
- `POST /public/geosphere/threshold/preview`
- `GET /public/geosphere/export-manifest`
- `GET /public/geosphere/readiness`

## Evidence boundaries

The public surface is labeled:

**SOLID-EARTH EVIDENCE · NOT AN EMERGENCY, DAMAGE OR HAZARD DETERMINATION**

The release enforces these boundaries:

- earthquake-catalog records may be revised; an event record is not a platform-issued emergency warning;
- ShakeMap is not converted into a building-by-building structural-damage census;
- PAGER impact estimates are not converted into confirmed loss;
- USGS volcano notices remain source-issued and are never reissued, escalated or downgraded by Sustainable Catalyst;
- aviation color codes remain source-attributed;
- InSAR line-of-sight displacement is not silently represented as vertical displacement;
- deformation evidence is not automatically converted into structural damage or causation;
- preliminary/rapid-response products remain distinct from final products;
- zero returned records do not mean no earthquake, volcano activity or solid-Earth hazard exists.

## Architecture

- Primary public areas: **6**
- Public routes: **35**
- New top-level route family: **none**
- Integration: deferred Earth Observation environment after Terrestrial Systems
- WordPress application viewport and host-page isolation: preserved
- Runtime-state manifest exclusion introduced after v4.12: preserved

## Deployment policy

The WordPress v4.20.0 plugin must not be installed until the macOS installer confirms that the exact v4.20.0 GitHub/Render release gate is live. The promotion gate independently verifies the Geosphere overview, four-source catalog, bounded empty earthquake state, readiness contract and shipped browser asset before release completion.
