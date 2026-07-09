# Changelog

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
