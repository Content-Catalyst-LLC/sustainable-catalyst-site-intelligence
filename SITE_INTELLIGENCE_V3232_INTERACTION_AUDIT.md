# Site Intelligence v3.23.6 interaction audit

## Baseline

v3.23.1 completed public-route truth and fixed the WordPress host-document false warning. The next completion requirement was to make the map understandable, filterable, selectable, and shareable without relying on surrounding prose.

## Production findings addressed

1. The overview map exposed imagery tabs and two binary toggles but no coherent layer catalog.
2. Event markers used only earthquake versus natural-event styling.
3. The event list and map were not synchronized.
4. Global views could become visually dense because records were not clustered.
5. Map center, zoom, filters, opacity, and selected record were not represented in the URL.
6. The WordPress host document had to remain isolated from standalone application runtimes.

## Implemented contract

- A self-contained layer and evidence-control panel is attached only to the Site Intelligence app root.
- Base presentation, imagery opacity, category, source, recency, event visibility, and clustering are explicit controls.
- Semantic symbols remain paired with labels in a visible legend.
- Event markers and list rows share stable record identifiers.
- Selecting a list row focuses and opens the corresponding map record.
- Selecting a map record updates the list selection and URL state.
- Clustering is deterministic at low zoom and expands by zooming toward the cluster.
- Empty filtered results retain geographic context and explain that only the overlay is empty.
- The route URL preserves map and evidence state without creating a hosted user profile.
- App-only scripts are packaged in WordPress but are not enqueued into the host document.

## Validation boundary

Automated validation proves packaged contracts, deterministic filtering, browser interaction, local geography, and syntax. Live third-party tile availability and changing upstream public records remain production conditions rather than immutable release guarantees.
