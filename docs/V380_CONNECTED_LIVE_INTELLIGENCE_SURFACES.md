# v3.8.0 — Connected Live Intelligence Surface

Live Intelligence now operates as one governed signal system with multiple bounded public presentations. The release does not create separate ingestion services for the homepage, Library, Advisory, Lab, publications, or embeds. Every surface uses the same source operations, validation, freshness, last-known-good recovery, gateway, rotation, evidence, accessibility, and aggregate analytics contracts.

## Public surfaces

| Surface | Purpose | Default presentation | Default limit |
|---|---|---:|---:|
| `homepage` | Primary homepage gateway | ticker | 8 |
| `static_strip` | Calm inline institutional strip | static | 6 |
| `channel` | Topic or region channel | manual | 10 |
| `publication` | Evidence-aware publication insert | static | 3 |
| `library` | Knowledge Library collection/pathway panel | manual | 6 |
| `advisory` | Advisory context without personalized-advice claims | static | 4 |
| `lab` | Scientific and environmental observations | manual | 8 |
| `external_embed` | Approved public-safe external embed | static | 6 |

## Governance

Surfaces may filter signal families, cap counts, and constrain destinations. They may not rewrite observations, remove freshness or lineage, expose private state, inject arbitrary signals, or add advertising and affiliate promotions. External embeds are approved only for surfaces whose policy explicitly enables embedding.

## Public endpoints

- `/public/live-intelligence/surfaces`
- `/public/live-intelligence/surface-policy`
- `/public/live-intelligence/surfaces/{surface_id}`
- `/public/live-intelligence/surfaces/{surface_id}/feed`
- `/public/live-intelligence/embed-manifest`

## WordPress

The general shortcode accepts all governed `surface` IDs. Preset aliases apply recommended motion, mobile, count, and label defaults while continuing to use the same WordPress proxy and backend.
