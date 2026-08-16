# Site Intelligence v4.36.0 R2 — Science Workspace Core-Decoupling & Ocean/Space Discovery Repair

R2 repairs the Science front door reported after the Ocean R1 release. The Scientific and Earth Systems Observatory was still using its v2.4-era Platform Core data-fabric model as the only source for dropdown values. When Platform Core was unconfigured, the page correctly refused to fabricate scientific records, but incorrectly became unusable as a navigation surface for newer v4.x Ocean and Space workspaces.

## Repair

- Adds a network-free `/public/scientific-earth-systems/discovery` contract.
- Keeps Earth, Ocean, and Space discoverable regardless of Platform Core configuration.
- Adds an always-populated Science domain selector with Earth, Ocean, and Space.
- Exposes eight local workspaces: Earth Observation, Ocean Intelligence, Orbital Earth, Lunar & Planetary Intelligence, Astronomical Observation, Solar System Navigation, Exoplanets & Atmospheres, and SETI & Technosignatures.
- Keeps Platform Core scientific records, assets, map layers, STAC items, and time series as an optional second layer.
- Disables only Core-backed record filters when Core is unconfigured; local Science discovery remains usable.
- Preserves the no-fabrication rule: no scientific records, observations, datasets, measurements, or claims are invented locally.
- Runtime and WordPress plugin versions remain `4.36.0`; repaired release lineage is `v4.36.0-r2`.
