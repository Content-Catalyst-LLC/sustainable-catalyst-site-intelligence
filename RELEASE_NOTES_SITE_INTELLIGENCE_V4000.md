# Site Intelligence v4.12.0 — Unified Public Intelligence Platform

## Release purpose

v4.12.0 is a consolidation release. It reorganizes the accumulated Site Intelligence capability set into one public intelligence platform without deleting, renaming, or silently migrating the existing public workspaces.

## Primary navigation

The 35 preserved routes are grouped into exactly six primary areas:

1. **Live Overview** — Overview, Global Conditions, Events, Alerts.
2. **Places & Systems** — Country, Dossiers, Economics, International Law, Science, Humanitarian, Resources, Thematic.
3. **Analysis** — Compare, Spatial Evidence, Earth Observation, Harmonization, Models, Scenarios.
4. **Evidence & Research** — Connected Platform, Observatory, Research Paths, Evidence, Graph, Sources, Saved.
5. **Publishing & Monitoring** — Briefing, Publishing, Monitoring, Workspaces.
6. **Methods & Operations** — Integration, Workflows, Federation, Governance, Experience, Launch.

The grouping is presentation architecture, not a second router. Existing route buttons, deep links, public endpoints, and WordPress shortcodes remain available.

## Canonical platform contracts

v4.12.0 identifies six shared contract families:

- route and cross-view state;
- Data Truth and record provenance;
- comparative/scenario/model assurance;
- research and cross-product handoffs;
- publication and export;
- operations and governance.

These contracts retain the prior safeguards: missing and stale data remain explicit, modeled outputs do not become automated decisions, handoffs require confirmation, and publication remains review-gated.

## New public endpoints

- `GET /public/v4`
- `GET /public/v4/navigation`
- `GET /public/v4/contracts`
- `GET /public/v4/readiness`

## Compatibility

- 35/35 existing public routes preserved.
- Existing public endpoints preserved.
- Existing WordPress shortcodes preserved.
- Deep links preserved.
- No automatic migration or destructive schema change.
- Future removals require a documented compatibility window.

## Browser integration

`unified-platform-v4000.js` groups the existing navigation in place, keeps the active area expanded, and exposes the v4 consolidation status in the Connected Platform workspace. The app remains fully usable in the standalone shell and fixed WordPress iframe.

## Deployment

The release bundle must pass checksum verification, immutable-manifest verification, the complete Python regression suite in an isolated environment, static/security checks, and the live GitHub/Render release gate before the WordPress ZIP is installed.
