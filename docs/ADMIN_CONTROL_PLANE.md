# Admin Control Plane

Site Intelligence v0.9.0 adds a private admin/control-plane layer for registry, source, module, shortcode, visibility, diagnostics, and source-control review.

## Backend endpoints

```text
/admin/registry
/admin/registry/coverage
/admin/sources
/admin/modules
/admin/shortcodes
/admin/diagnostics
/admin/visibility
/admin/source-control
/intelligence/admin
```

All backend admin endpoints require the existing Site Intelligence API token in production.

## WordPress shortcodes

```text
[sc_site_intelligence_admin_overview]
[sc_site_intelligence_shortcode_catalog]
[sc_site_intelligence_module_status]
```

These should remain private/admin-only.

## Source-control posture

v0.9.0 is intentionally read-only. It identifies managed files and recommended Git workflow but does not edit registry/source files from WordPress.

Future releases can add a guarded editor, diff preview, validation, and commit/export workflow.
