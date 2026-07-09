# SEO Intelligence Notes

v0.3.1 adds Metadata, Titles, and Internal Link Intelligence.

## Metadata Intelligence

The metadata layer prioritizes pages using:

- Search Console impressions
- CTR
- average position
- title length
- generic/archive/error title signals
- query-title token overlap
- registry mapping status

The build does not crawl rendered HTML meta descriptions. It flags pages that deserve manual title/meta review.

## Internal Link Intelligence

The internal-link layer prioritizes pages using:

- impressions
- CTR
- average position
- near-position opportunity, especially positions 6–20
- registry mapping status
- article-map/hub relationships
- intended next paths
- repository URLs
- Workbench tool IDs

## Combined SEO Recommendations

The combined recommendation queue merges metadata and link priorities into one action list for editorial workflow.
