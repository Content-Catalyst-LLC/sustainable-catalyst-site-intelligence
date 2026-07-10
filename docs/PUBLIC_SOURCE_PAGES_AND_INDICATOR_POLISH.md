# Public Source Pages and Indicator Integration Polish — v1.2.1

Site Intelligence v1.2.1 turns the v1.2.0 public API/source layer into a cleaner public page system.

## Public source page paths

- `/platform/site-intelligence/sources/`
- `/platform/site-intelligence/source-health/`
- `/platform/site-intelligence/indicators/`
- `/platform/site-intelligence/sustainability-indicators/`
- `/platform/site-intelligence/research-metadata/`
- `/platform/site-intelligence/publication-metadata/`
- `/platform/site-intelligence/repository-intelligence/`

## New public endpoints

- `/public/source-pages`
- `/public/source-pages/navigation`
- `/public/source-pages/templates`
- `/public/source-pages/visual-qa`

## New WordPress shortcodes

- `[sc_public_source_page_directory]`
- `[sc_public_source_navigation]`
- `[sc_public_source_page_templates]`
- `[sc_public_source_page_visual_qa]`

## Recommended public page pattern

Each source page should use a custom `cc-platform-v5 ccp-site-intelligence-public` shell, then include:

1. Hero section
2. `[sc_public_source_navigation current="page-slug"]`
3. The relevant source panel shortcode
4. What the page shows
5. Methodology and boundaries
6. Related source pages
7. Footer links back to Site Intelligence, Dashboard Directory, Source Methodology, and Platform

## Public boundaries

Public source pages must not expose API credentials, raw upstream payloads, force-refresh logs, private analytics, admin diagnostics, unreleased reports, internal review notes, or professional assurance claims.
