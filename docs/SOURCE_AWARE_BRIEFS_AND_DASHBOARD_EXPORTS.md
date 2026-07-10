# Source-Aware Briefs and Dashboard Exports

Version: v1.5.0

This build adds a public-safe brief and export layer on top of the Site Intelligence dashboard, source, connector, and indicator chart systems.

## Public endpoints

- `/public/source-aware-briefs`
- `/public/source-aware-briefs/site-intelligence`
- `/public/source-aware-briefs/indicator`
- `/public/source-aware-briefs/source-health`
- `/public/dashboard-exports`
- `/public/dashboard-exports/manifest`
- `/public/dashboard-exports/site-intelligence`
- `/public/dashboard-exports/indicator`
- `/public/dashboard-exports/source-health`
- `/public/dashboard-exports/visual-qa`

## WordPress shortcodes

- `[sc_public_source_aware_brief_directory]`
- `[sc_public_site_intelligence_source_brief]`
- `[sc_public_indicator_source_brief]`
- `[sc_public_source_health_brief]`
- `[sc_public_dashboard_export_manifest]`
- `[sc_public_site_intelligence_export]`
- `[sc_public_indicator_dashboard_export]`
- `[sc_public_source_health_export]`
- `[sc_public_dashboard_export_visual_qa]`

## Public safety policy

The export layer cites public Site Intelligence endpoints and source-family summaries. It does not expose API keys, raw upstream payloads, private analytics rows, admin diagnostics, or professional assurance conclusions.
