# Public Indicator Dashboards and Chart Layer

Site Intelligence v1.4.0 adds chart-ready public indicator dashboards for sustainability, development indicators, source health, research metadata, and repository intelligence.

## Public endpoints

- `/public/indicator-dashboards`
- `/public/indicator-dashboards/sustainability`
- `/public/indicator-dashboards/development`
- `/public/indicator-dashboards/source-health`
- `/public/indicator-dashboards/research`
- `/public/indicator-dashboards/repository`
- `/public/indicator-dashboards/charts`
- `/public/indicator-dashboards/visual-qa`

## Public shortcodes

- `[sc_public_indicator_dashboard_directory]`
- `[sc_public_sustainability_indicator_dashboard]`
- `[sc_public_development_indicator_dashboard]`
- `[sc_public_source_health_chart_dashboard]`
- `[sc_public_research_metadata_chart_dashboard]`
- `[sc_public_repository_chart_dashboard]`
- `[sc_public_indicator_chart_gallery]`
- `[sc_public_indicator_chart_visual_qa]`

The chart layer uses public-safe summary payloads and WordPress fallback rendering. It does not expose API credentials, raw upstream payloads, private analytics, admin connector diagnostics, or professional assurance determinations.
