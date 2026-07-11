# Site Intelligence v2.0.0 — Auditable Public Observatory

## Purpose

The major release turns the public product into an auditable observatory. The new layer does not replace the source, methodology, country, event, Earth-observation, comparison, thematic, briefing, saved-view, or launch workspaces. It publishes a reviewable contract across them.

## Public evidence record

Each registered record publishes:

- stable artifact ID and artifact type
- public route and artifact schema
- application and API schema versions
- source record IDs
- methodology record IDs
- verification level and data state
- known limitations
- canonical SHA-256 digest

The digest scope excludes `generated_at` and the integrity envelope so repeated requests produce the same digest for the same substantive record.

## Lineage graph

The public lineage graph uses four node types:

1. source
2. methodology
3. audit artifact
4. public workspace

Relations are explicit: sources support artifacts, methods govern artifacts, and artifacts document workspaces.

## Verification contract

`POST /public/observatory/verify` accepts a JSON payload and an optional expected digest. The backend canonicalizes the payload, computes SHA-256, reports whether it matches, and does not persist the request. Payloads larger than 256 KiB or containing sensitive-field names are rejected.

A matching digest does not prove factual correctness, publisher identity, legal authenticity, source availability, or completeness.

## Public endpoints

- `/public/observatory`
- `/public/observatory/catalog`
- `/public/observatory/audit/{artifact_id}`
- `/public/observatory/lineage`
- `/public/observatory/verification`
- `/public/observatory/verify`
- `/public/observatory/release-ledger`
- `/public/observatory/diagnostics`
- `/public/observatory/export`

## WordPress

```text
[sc_auditable_public_observatory height="1250"]
```

The primary flagship application remains:

```text
[sc_site_intelligence_app height="1000"]
```

The old country, comparison, and geospatial preview implementations are retired. Their shortcode names remain as compatibility aliases to the modern standalone workspaces so existing pages do not fail during migration.

## Infrastructure boundary

No account system, telemetry vendor, paid database, Redis service, proprietary map service, digital-signature service, or additional Render service is required. Platform Core remains optional.
