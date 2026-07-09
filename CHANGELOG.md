# Changelog

## v0.7.0 — Report Generator and Export Intelligence

Adds an internal reporting and export layer on top of Site Intelligence dashboards.

### Added

- Weekly Site Intelligence report generator.
- Search Intelligence report generator.
- Content Strategy and Publishing report generator.
- External Data Sources report generator.
- Climate + Energy Snapshot report generator.
- Registry and Indexing Coverage report generator.
- Combined export bundle endpoint.
- JSON, Markdown, and CSV export formats.
- WordPress report shortcodes for private planning pages.
- Report methodology, privacy notes, highlights, recommendations, and section rows.

### New backend endpoints

- `/reports/site-intelligence`
- `/reports/search-intelligence`
- `/reports/content-strategy`
- `/reports/external-sources`
- `/reports/climate-energy`
- `/reports/indexing`
- `/reports/export`
- `/intelligence/reports`

### New WordPress shortcodes

- `[sc_site_intelligence_report]`
- `[sc_search_intelligence_report]`
- `[sc_content_strategy_report]`
- `[sc_external_sources_report]`
- `[sc_climate_energy_report]`
- `[sc_indexing_report]`
- `[sc_report_export_bundle]`

### Notes

- Report endpoints are protected by the same `SC_SI_API_TOKEN` as the internal dashboard endpoints.
- Public pages should continue to use the public dashboard shortcodes rather than raw report outputs.
- Markdown/CSV exports are intended for internal planning, GitHub documentation drafts, editorial notes, and spreadsheet review.
