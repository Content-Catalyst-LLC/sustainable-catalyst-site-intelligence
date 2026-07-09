# Changelog

## v0.9.0 — Admin Registry Manager and Source Control Tools

Adds the Site Intelligence admin control plane.

### Added

- Registry Manager endpoint: `/admin/registry`
- Registry coverage endpoint: `/admin/registry/coverage`
- Source Manager endpoint: `/admin/sources`
- Module Manager endpoint: `/admin/modules`
- Shortcode Catalog endpoint: `/admin/shortcodes`
- Diagnostics endpoint: `/admin/diagnostics`
- Visibility Matrix endpoint: `/admin/visibility`
- Source Control Tools endpoint: `/admin/source-control`
- Combined admin overview endpoint: `/intelligence/admin`
- WordPress shortcode: `[sc_site_intelligence_admin_overview]`
- WordPress shortcode: `[sc_site_intelligence_shortcode_catalog]`
- WordPress shortcode: `[sc_site_intelligence_module_status]`
- JavaScript renderers for admin overview, module status, and shortcode catalog
- WordPress admin settings-page references for new control-plane shortcodes
- Backend tests for v0.9.0 admin endpoints and shortcode catalog

### Notes

- v0.9.0 is read-only for registry/source control. It does not write to registry files from WordPress.
- Admin WordPress REST proxy routes require `manage_options`.
- Backend admin routes remain protected by the existing `SC_SI_API_TOKEN` in production.

## v0.8.2 — Public Dashboard Brief Local Fallback Patch

Stabilized the public dashboard brief shortcode with a local WordPress fallback.

## v0.8.1 — Public Dashboard Brief Gateway Patch

Suppressed raw Cloudflare/host gateway HTML in AI brief rendering.

## v0.8.0 — AI-Assisted Intelligence Briefs

Added AI-assisted brief endpoints, deterministic fallback briefs, optional Gemini support, and WordPress AI brief shortcodes.
