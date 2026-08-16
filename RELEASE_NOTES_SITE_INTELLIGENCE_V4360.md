# Site Intelligence v4.36.0 R1 — Ocean Navigation Runtime & Browser Certification Repair

## Repair purpose

v4.36.0 R1 repairs the browser-certification failure found after the original Global Ocean Intelligence II build passed its backend, static, security, manifest, and 1,667-test regression gates. The Ocean backend contract remains unchanged at version `4.36.0`; this repair is deliberately limited to navigation ownership, browser-shell fixtures, route aliasing, and certification behavior.

## Root cause repaired

The v4 six-area navigation runtime reconstructs `#primaryNavigation` from the 35 canonical `[data-route]` buttons. The new Ocean entry is intentionally a supplemental workspace under the existing Earth route, so it has no 36th canonical `data-route`. During regrouping, the runtime therefore discarded the Ocean button even though it was present in the shipped HTML.

After preserving that control, browser validation exposed two adjacent certification defects: a preserved Ocean control nested inside a closed accordion was technically present but not visible, and the deterministic complete-shell harness did not include the new Ocean fetch fixtures. R1 repairs all three boundaries rather than weakening the smoke test.

## Runtime changes

- Ocean is retained as a **featured workspace control** above the six collapsible navigation groups.
- The canonical v4 contract remains **6 primary areas / 35 routes**; Ocean continues to use `view=earth&oceanMode=hub`.
- Ocean carries `data-route-alias="earth"`, allowing shared cartographic visibility logic to treat the supplemental workspace as an Earth-route mode even when deterministic browser tests disable History API mutation.
- The v4 navigation grouper now preserves first-class supplemental controls instead of deleting every non-`data-route` navigation item.
- Ocean opening no longer waits for Earth imagery initialization. A degraded Earth imagery service can therefore not prevent the Ocean hub, catalog, readiness state, or system cards from opening.
- The complete-shell deterministic fetch fixture now includes Ocean catalog/readiness contracts and Earth route fixtures needed by the Ocean browser path.
- Backend and WordPress copies of the repaired navigation, cartographic, and Ocean assets remain byte-identical.

## Browser certification

R1 verifies the post-regrouping runtime rather than the raw source HTML. The Ocean browser gate requires:

- a visible featured Ocean navigation control after v4 navigation consolidation;
- Ocean active / Earth inactive navigation state;
- visible Ocean workspace shell;
- 11 system cards across 5 groups;
- visible Data Truth boundary;
- `Ocean observation & marine systems` workspace title;
- no page errors.

The complete production-shell gate also passes with service workers disabled, service-worker registration failure, and iframe embedding while preserving 6 groups, 35 routes, runtime readiness, and bounded observer behavior.

## Preserved Ocean systems

1. Ocean Surface
2. Water Column & Depth
3. Seafloor & Bathymetry
4. Underwater Observation
5. Marine Biodiversity & Bioacoustics
6. Missions, Vehicles & Observatories
7. Ocean Events & Hazards
8. Marine Human Activity
9. Marine Pollution & Water Quality
10. Coastal Change & Sea Level
11. Ocean Governance & Maritime Boundaries

## Release identity

- Backend version: `4.36.0`
- WordPress plugin version: `4.36.0`
- Release ID: `site-intelligence-v4.36.0`
- Repair designation: `R1`
- Canonical primary areas: `6`
- Canonical routes: `35`
- Ocean route delta: `0`
