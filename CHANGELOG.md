# Changelog

## v0.8.0 — AI-Assisted Intelligence Briefs

- Added AI status endpoint and provider-disabled default behavior.
- Added deterministic fallback briefs that require no external AI model.
- Added optional Gemini brief generation with safe fallback on provider failure or timeout.
- Added token-protected AI brief endpoints for Site Intelligence, Search, Publishing, External Sources, and Public Dashboard interpretation.
- Added Markdown output support for AI briefs.
- Added WordPress AI brief shortcodes and frontend rendering.
- Added public/private brief modes and public-safe summary fields.


## v0.7.1 — Export Bundle Timeout Patch

- Changed `/reports/export` to return a lightweight WordPress-safe export manifest by default.
- Added `full=true` support for complete combined export bundles when called directly from Terminal/internal workflows.
- Added explicit export-mode guidance to the report manifest.
- Preserved individual report endpoints for JSON, Markdown, and CSV exports.
- Added a regression test for the lightweight export-manifest report shape.

## v0.7.0 — Report Generator and Export Intelligence

- Added internal report generator endpoints for Site Intelligence, Search Intelligence, Content Strategy, External Sources, Climate + Energy, and Indexing.
- Added JSON, Markdown, and CSV export support.
- Added WordPress report shortcodes for private/internal planning pages.
