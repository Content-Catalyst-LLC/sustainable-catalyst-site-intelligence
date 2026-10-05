# Site Intelligence v4.49.0 — Live Geospatial Event Fusion

v4.49.0 adds a provenance-preserving execution layer for live and near-real-time geospatial events on top of the v4.46 evidence registry, v4.47 spatiotemporal engine, and v4.48 infrastructure graph.

## New contracts

- `sc-site-intelligence-live-geospatial-event/1.0`
- `sc-site-intelligence-live-event-cluster/1.0`
- `sc-site-intelligence-live-geospatial-fusion-result/1.0`
- `sc-site-intelligence-live-event-graph-fusion/1.0`
- `sc-site-intelligence-live-geospatial-snapshot/1.0`

## New modular API

- `GET /public/live-geospatial/registry`
- `GET /public/live-geospatial/event-schema`
- `GET /public/live-geospatial/sources`
- `GET /public/live-geospatial/lifecycle`
- `POST /public/live-geospatial/events/normalize`
- `POST /public/live-geospatial/events/normalize-source`
- `POST /public/live-geospatial/events/reconcile`
- `POST /public/live-geospatial/events/query`
- `POST /public/live-geospatial/lifecycle/transition`
- `POST /public/live-geospatial/fuse/layers`
- `POST /public/live-geospatial/fuse/graph`
- `POST /public/live-geospatial/snapshot`
- `GET /public/live-geospatial/compatibility`

## Source adapters

The first certified adapters normalize USGS earthquake GeoJSON, NASA EONET v3 events, and geospatial NOAA/NWS alerts. ReliefWeb and platform-status records can participate through the generic adapter when a source record provides explicit geometry.

## Evidence boundaries

Spatial intersection and temporal overlap are fusion signals, not proof of damage, causality, or confirmed impact. Graph fusion produces ephemeral `potentially-exposed-to-event` relationships without mutating the v4.48 source graph. Cross-source reconciliation is strict and deterministic and does not perform hidden fuzzy merging.

## Runtime inventory

v4.49.0 advances the capability registry to `1.6.0` and certifies 1,399 total routes, 90 modularized routes, 20 capability families, 13 modular live-geospatial routes, and zero unclassified routes.
