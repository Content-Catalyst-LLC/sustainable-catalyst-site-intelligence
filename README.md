# Sustainable Catalyst Site Intelligence

Version: 0.10.1

Site Intelligence is the Sustainable Catalyst analytics, registry, external-source, reporting, AI-brief, public-dashboard, and admin-control platform.

## v0.10.1 highlights

- Public dashboard visual QA layer
- Copy polish guidance for the flagship public page
- Mobile spacing and card-stacking QA notes
- Safer public empty/error state presentation
- Public page title, excerpt, and meta-description suggestions
- Private/review shortcode for launch-readiness checks

## New backend endpoint

- `/public/page-builder/visual-qa`

## New private/review shortcode

- `[sc_public_dashboard_visual_qa]`

Keep visual QA, page-builder, readiness, reports, AI briefs, Search Console, and GA4 shortcodes on private/review pages unless manually approved.


## v0.10.1 — Public Flagship Dashboard Page Builder

Adds a public-safe page-builder layer for assembling the flagship Sustainable Catalyst Site Intelligence dashboard.

New public endpoints:

- `/public/page-builder`
- `/public/page-builder/shortcodes`
- `/public/page-builder/readiness`
- `/intelligence/public-page-builder`

New WordPress shortcodes:

- `[sc_site_intelligence_public_flagship]`
- `[sc_site_intelligence_public_page_builder]`
- `[sc_public_dashboard_shortcode_bundle]`

The flagship shortcode uses only public-safe modules and local presentation copy by default.


## v0.10.1 — Public Dashboard Visual QA and Copy Polish

Adds a final public dashboard quality-assurance layer before v1.0 public release.

New public-safe review endpoint:

- `/public/page-builder/visual-qa`

New private/review shortcode:

- `[sc_public_dashboard_visual_qa]`

Use this shortcode on an internal review page to check copy tone, visual hierarchy, mobile spacing, public/private boundaries, and launch polish before promoting the flagship dashboard publicly.
