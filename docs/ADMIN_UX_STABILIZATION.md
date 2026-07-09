# Site Intelligence v0.9.1 Admin UX and Diagnostic Stabilization

v0.9.1 adds a more usable WordPress admin/control-plane layer for verifying backend health, protected endpoint access, shortcode placement, public/private visibility, and diagnostic readiness.

New backend endpoints:

- `/admin/status`
- `/admin/connection-check`
- `/admin/public-readiness-check`
- `/admin/diagnostic-summary`

New private shortcodes:

- `[sc_site_intelligence_diagnostic_summary]`
- `[sc_site_intelligence_connection_check]`

These panels are intended for admin/private pages only.
