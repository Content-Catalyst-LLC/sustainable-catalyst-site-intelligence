# Site Intelligence v2.11.0 — Public Data API, Embeds, and Institutional Integration

## Public API

Base path: `/api/public/v1`. The API is read-only, versioned, and limited to sanitized public records and manifests. It never exposes provider credentials or private ingestion configuration.

## Embeds

Use `/api/public/v1/embed` to generate a bounded iframe manifest, or use `[sc_site_intelligence_embed]` in WordPress. Embed modes support system, light, and dark themes with full, compact, or hidden application chrome.

## Institutional integration

Institutional name, website, logo, contact, and accent are public presentation metadata only. They cannot change source attribution, licenses, methodology, values, dates, or quality states.
