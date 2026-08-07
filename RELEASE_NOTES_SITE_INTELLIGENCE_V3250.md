# Site Intelligence v3.25.0 — Unified Analytical Workspace and Cross-View State

## Release purpose

v3.25.0 connects Global Conditions, Country Intelligence, Compare, Spatial Evidence, Earth Observation, and the overview map through one portable analytical-state contract. It preserves country, comparison, indicator, imagery, date, and spatial selections when users move between compatible workspaces.

## New public contracts

- `GET /public/workspaces/unified-state`
- `POST /public/workspaces/unified-state/normalize`
- `POST /public/workspaces/unified-state/deep-link`
- `POST /public/workspaces/unified-state/handoff/{target}`

## Browser capabilities

- Persistent country and analytical selections across supported workspaces
- Route-specific canonical deep links
- Local and session persistence without an account or server-side profile
- Direct handoffs among Global, Country, Compare, Spatial, and Earth workspaces
- A compact state bar that discloses the active country, workspace, and state fingerprint
- Portable link copying without claiming that the link freezes underlying data

## Preserved boundaries

- A deep link preserves interface state; it is not a data snapshot.
- Cross-view state does not claim that every destination has matching records.
- Invalid countries and routes fail closed to disclosed defaults.
- Comparison countries remain distinct.
- Missing records are never borrowed from another country.
- Country Truth, Record Truth, and the Global Data Truth Control Plane remain authoritative for availability, freshness, and provenance.
