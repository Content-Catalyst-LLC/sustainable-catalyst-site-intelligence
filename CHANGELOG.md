# Changelog

## v0.8.2 — Public Dashboard Brief Local Fallback Patch

- Makes `[sc_ai_public_dashboard_brief]` render a local deterministic public-safe brief by default.
- Adds `live="true"` as an opt-in backend route test mode for the public-dashboard AI brief.
- Updates the WordPress REST proxy to return a local public-safe fallback when the backend/proxy returns a gateway error.
- Adds a browser-side fallback for the public-dashboard brief if the REST call fails.
- Changes the backend public-dashboard AI brief endpoint to deterministic mode by default (`use_ai=false`).
- Adds a backend fallback response instead of returning a 502 if public-dashboard brief assembly fails.
- Keeps raw analytics, live connectors, and AI-provider calls out of the default public-dashboard brief rendering path.

## v0.8.1 — Public Dashboard Brief Gateway Patch

- Suppressed raw HTML gateway errors in WordPress output.
- Moved the public-dashboard brief toward a fast public-safe source report.

## v0.8.0 — AI-Assisted Intelligence Briefs

- Added AI brief provider status.
- Added deterministic fallback briefs.
- Added optional Gemini support.
- Added Site Intelligence, Search, Publishing, External Sources, and Public Dashboard brief endpoints and shortcodes.
