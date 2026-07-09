# Changelog

## v0.8.1 — Public Dashboard Brief Gateway Patch

- Patched the AI Public Dashboard Brief source report so it no longer calls live analytics-backed dashboard generation during shortcode render.
- Uses a fast public-safe snapshot built from landing-page, methodology, and readiness data.
- Suppresses raw Cloudflare/HTML gateway error bodies in the WordPress proxy response.
- Adds frontend error sanitization so upstream HTML error pages are never printed into Site Intelligence cards.
- Keeps `[sc_ai_public_dashboard_brief]` as the same shortcode.

## v0.8.0 — AI-Assisted Intelligence Briefs

- Added AI-assisted brief endpoints and shortcodes.
- Added deterministic fallback briefs with optional Gemini support.
