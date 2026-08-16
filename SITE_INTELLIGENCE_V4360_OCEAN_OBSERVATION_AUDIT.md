# Site Intelligence v4.36.0 — Ocean Observation Architecture Audit

## Finding

Ocean capabilities were already broad in the v4.35.25 repository but were difficult to discover because the public experience entered the marine stack through Earth Observation and progressively chained specialized modules. v4.36.0 resolves the discoverability problem by adding a first-class Ocean entry and a composition layer rather than duplicating mature implementation.

## Architecture decision

**Preserve the v4 six-area / 35-route contract.** Ocean operates as a first-class mode of the canonical `earth` route:

`/app/?view=earth&oceanMode=hub`

This avoids creating a 36th canonical route while still making Ocean independently visible in navigation, launch surfaces, URL state and saved views.

## Composed marine systems

| System | Existing public contract | Role in v4.36.0 |
|---|---|---|
| Ocean Surface | `/public/ocean-intelligence` | Physical surface conditions and derived products |
| Water Column | `/public/water-column` | Depth/profile observations |
| Seafloor | `/public/seafloor-intelligence` | Bathymetry, terrain and survey evidence |
| Underwater Observation | `/public/underwater-observation` | ROV/AUV imagery, video and annotation evidence |
| Marine Biodiversity | `/public/marine-biodiversity` | Occurrence, taxonomy and acoustic/visual evidence |
| Ocean Missions | `/public/ocean-missions` | Floats, gliders, vessels and observatories |
| Ocean Events | `/public/ocean-events` | Hazards, heatwaves and ecosystem-stress events |
| Marine Human Activity | `/public/marine-human-activity` | Vessel, fishing, protected-area and pressure context |
| Marine Pollution | `/public/marine-pollution` | Pollution, litter, contaminants and water-quality evidence |
| Coastal Change | `/public/coastal-change` | Tides, water levels, shoreline and sea-level context |
| Ocean Governance | `/public/ocean-governance` | Maritime-zone and fisheries-governance orientation |

## New composition contract

`backend/app/ocean_observation_marine_systems_v4360.py` aggregates inherited catalogs/readiness surfaces into four new network-free endpoints. It reports source registrations, capability groups, browser assets, truth boundaries and readiness without performing upstream calls.

## Public UI decision

`ocean-observation-v4360.js` owns the Ocean hub and direct system launch. It loads existing specialized scripts only when requested and calls their established `enter()` methods. No legacy Ocean module is reimplemented.

## Release invariants

- Six primary areas remain intact.
- Canonical route count remains 35.
- Ocean has an explicit public navigation entry.
- Existing Ocean endpoints remain valid.
- Existing Ocean modules retain their evidence models and source semantics.
- Missing data is not converted to zero or inferred replacement values.
- Network-free release verification is separate from live upstream source health.

## R1 browser-certification repair

R1 verified that the original HTML Ocean entry was lost when the v4 navigation grouper rebuilt `#primaryNavigation` from only canonical `[data-route]` controls. The repair preserves supplemental first-class controls and promotes Ocean into a permanently visible featured-workspace band above the six collapsible groups. `data-route-alias="earth"` preserves the existing route model, and Ocean initialization no longer waits for Earth imagery services. The complete-shell browser harness was also updated to current `4.36.0` identity and Ocean/Earth deterministic fixtures.
