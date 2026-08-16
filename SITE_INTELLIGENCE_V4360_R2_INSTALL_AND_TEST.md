# Site Intelligence v4.37.0 R2 — Install and Test

## Release identity

- Runtime/plugin version: `4.37.0`
- Repair lineage: `R2`
- Git tag: `v4.37.0`
- Release: **Science Workspace Core-Decoupling & Ocean/Space Discovery Repair**

## What this repairs

The Science front door no longer requires Platform Core merely to discover or launch Site Intelligence science workspaces. Earth, Ocean, and Space are always available from the local Site Intelligence application. Platform Core remains optional and supplies the separate scientific-record/data-fabric catalog when configured.

No scientific records, measurements, observations, datasets, or claims are fabricated when Core is unavailable.

## Required certification

The release verifier checks:

1. immutable manifest integrity;
2. JSON/GeoJSON, JavaScript, Python, and WordPress/PHP static integrity;
3. security scan;
4. all 1,672 deterministic backend tests;
5. Ocean browser certification;
6. Science/Core-decoupling browser certification;
7. inherited country and workspace browser gates.

## Production behavior to confirm

Open **Science** and verify:

- the first selector contains `Earth`, `Ocean`, and `Space` even when Platform Core is unconfigured;
- choosing **Ocean** exposes and opens Ocean Intelligence;
- choosing **Space** exposes Orbital Earth, Lunar & Planetary, Astronomy, Solar System, Exoplanets, and SETI;
- Core-backed record filters may be disabled when Core is unconfigured, but the Science discovery interface remains usable.
