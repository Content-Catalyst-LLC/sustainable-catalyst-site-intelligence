# Site Intelligence v4.45.0 Release Certification

Release: **WordPress Thin-Shell & Embed Bridge**

The release is certified when:

- FastAPI remains canonical product authority and `/app/` remains the canonical application.
- `/public/integrations/wordpress/{bridge,embed-contract,auth-handoff,compatibility}` are present in the modular `wordpress-integration` capability family.
- WordPress identifies itself as `thin-shell-and-embed-bridge` and exposes only integration-facing new REST surfaces.
- canonical embed URLs carry release, surface, bridge, and bridge-contract markers without credentials.
- browser bridge messages are versioned and accepted only from the iframe's expected origin.
- the protected `sc_site_intelligence_embed` compatibility shortcode renders without invalid `$this` usage.
- all 27 release-bound static policy files report v4.45.0 while historical origin metadata remains unchanged.
- the 72-shortcode compatibility ceiling remains exact; no new feature-specific shortcode is introduced.
- Contabo deployment preserves dynamic data and overlays current release-bound policies.
