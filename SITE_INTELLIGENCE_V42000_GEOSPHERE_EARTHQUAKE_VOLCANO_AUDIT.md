# Site Intelligence v4.20.0 — Geosphere, Earthquake & Volcano Audit

## Purpose

Add source-bounded solid-Earth intelligence without creating an unofficial warning service or collapsing fundamentally different evidence classes into a single hazard claim.

## Source registry

### USGS Earthquake Catalog & Real-time Feeds
- Registry id: `usgs-earthquake-catalog`
- Primary machine interface: USGS FDSN Event Web Service / real-time GeoJSON feeds
- Evidence: seismic event catalog, real-time event feed
- Boundary: preferred origins, magnitudes and review state may change; catalog presence is not a Sustainable Catalyst warning.

### USGS ShakeMap & PAGER
- Registry id: `usgs-shakemap`
- Evidence: modeled/observation-constrained shaking products and source-issued impact estimates
- Boundary: shaking intensity is not a structural-damage census; PAGER is not confirmed loss.

### USGS Volcano Hazards Program HANS
- Registry id: `usgs-volcano-hans`
- Evidence: Volcano Activity Notices, aviation notices/color codes, observatory status
- Boundary: USGS remains the issuing authority. Site Intelligence does not create, escalate, downgrade or supersede source alerts.

### NASA/JPL ARIA
- Registry id: `nasa-jpl-aria`
- Evidence: InSAR displacement / rapid-response deformation products
- Boundary: radar line-of-sight displacement is not automatically vertical motion, damage, causation or a hazard declaration; coherence/unwrapping/preliminary limitations remain visible.

## Indicator classes

Earthquake event; magnitude; depth; review status; PAGER alert; shaking intensity; peak ground acceleration; peak ground velocity; volcano alert level; aviation color code; volcano notice; eruption status; ground displacement; interferometric coherence; coseismic deformation; volcanic deformation.

## Public safety and legal truth gates

- `catalog_event_equals_emergency_warning = false`
- `shakemap_equals_structural_damage = false`
- `pager_equals_confirmed_loss = false`
- `source_volcano_alert_reissued_by_platform = false`
- `insar_equals_vertical_displacement = false`
- `insar_equals_damage = false`
- `preliminary_equals_final = false`
- `zero_records_equals_no_hazard = false`

## Release architecture

The environment remains inside Earth Observation. Six primary areas and all 35 public routes are preserved. No emergency dispatch, automatic action, navigation instruction, structural-safety determination or source-warning substitution is introduced.
