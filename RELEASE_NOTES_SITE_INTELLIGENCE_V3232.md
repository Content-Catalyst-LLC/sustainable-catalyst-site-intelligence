# Site Intelligence v3.23.6.3

## Cartographic Interaction and Layer Control

This release finishes the primary map as an analytical control surface rather than a passive background.

### Delivered

- Layer and evidence-control panel inside the map workspace.
- Institutional dark, evidence-neutral, and imagery-focus base presentations.
- Satellite imagery opacity control.
- Semantic event categories for earthquakes, fires, storms, floods, humanitarian records, conflict records, and other public events.
- Magnitude- and severity-aware marker treatment.
- Global-zoom event clustering with zoom-to-reveal behavior.
- Category, source, recency, visibility, and clustering filters.
- Synchronized event-list and map selection.
- Fit-to-results, filter reset, and shareable map URL state.
- Persistent map center, zoom, imagery, filter, cluster, and selected-record state.
- Map interaction contract at `/public/maps/interaction`.
- WordPress host isolation retained: app-only production-truth and interaction runtimes are packaged but are not executed in the WordPress host document.
- Runtime health, offline shell, GitHub promotion, and Render verification expanded to require the v3.23.6.3 interaction assets and contract.

### Responsible-use boundaries

Clusters summarize density rather than severity or importance. Filters do not imply that excluded records do not exist. Shared URLs preserve interface state, but they do not freeze changing upstream source data.
