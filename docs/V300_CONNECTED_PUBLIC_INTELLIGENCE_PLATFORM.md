# Connected Public Intelligence and Evidence Platform

## Purpose

v3.0.0 creates a single public discovery and provenance layer across Site Intelligence without flattening evidence types or bypassing the governance controls introduced throughout v2.x.

## Public API

- `GET /public/connected-intelligence`
- `GET /public/connected-intelligence/search?q=`
- `GET /public/connected-intelligence/context/{record_id}`
- `GET /public/connected-intelligence/provenance/{record_id}`
- `GET /public/connected-intelligence/lifecycle`
- `GET /public/connected-intelligence/diagnostics`
- `GET /public/connected-intelligence/export?q=&format=json|csv`

## Administrative API

- `GET /admin/connected-intelligence/control-center`
- `POST /admin/connected-intelligence/reindex-preview`

Administrative reindexing is preview-only in the default zero-cost implementation. It does not claim a persistent external search service or remote write.

## WordPress

- `[sc_connected_public_intelligence]`
- `[sc_connected_intelligence_control_center]`

The control-center shortcode is administrator-only.
