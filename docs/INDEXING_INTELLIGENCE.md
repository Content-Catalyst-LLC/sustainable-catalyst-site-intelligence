# Sitemap, Indexing, and Registry Coverage Intelligence

Site Intelligence v0.3.2 compares four operational views of Sustainable Catalyst:

1. XML sitemap URLs
2. Site Intelligence registry entries
3. GA4 page visibility
4. Google Search Console page visibility

It helps identify structural issues such as search-visible unmapped pages, traffic-visible pages missing from the registry, sitemap URLs missing from the registry, registry pages missing from the sitemap, 404 candidates, archive routing issues, and orphan candidates.

## Endpoints

```text
/indexing/sitemap
/indexing/coverage
/indexing/orphans
/indexing/404s
/indexing/recommendations
/intelligence/indexing
```

All endpoints require the `X-SC-Intelligence-Token` header in production.

## WordPress shortcodes

```text
[sc_indexing_intelligence]
[sc_sitemap_coverage]
[sc_404_intelligence]
```

## Optional Render variables

```text
SC_SI_SITEMAP_LIVE=true
SC_SI_SITEMAP_URL=https://sustainablecatalyst.com/sitemap.xml
SC_SI_SITEMAP_TIMEOUT_SECONDS=10
SC_SI_SITEMAP_MAX_URLS=500
SC_SI_SITE_BASE_URL=https://sustainablecatalyst.com
```

## Coverage statuses

- `covered`: page appears structurally aligned across sitemap/registry and has GA4 or Search Console visibility.
- `search_visible_unmapped`: page appears in Search Console but is not mapped to the registry.
- `traffic_unmapped`: page appears in GA4 but is not mapped to the registry.
- `sitemap_unmapped`: page appears in the sitemap but is not mapped to the registry.
- `registry_not_in_sitemap`: page is registered but not found in the fetched sitemap.
- `registry_inactive`: page is registered but has no reviewed GA4 or Search Console visibility.
- `diagnostic`: likely 404 or diagnostic routing issue.
- `partial`: mixed signal requiring review.

## Important limitation

This module does not claim to inspect Google's live index directly. It uses sitemap, GA4, Search Console performance, and registry signals. A future build can add URL Inspection API support for selected pages with quota controls.
