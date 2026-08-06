# Site Intelligence v3.23.6.3 Embed Isolation Audit

The complete application uses a fixed WordPress viewport. Parent and child height negotiation is disabled for `[sc_site_intelligence_app]`; internal application scrolling remains enabled. Document-oriented embeds retain bounded responsive sizing.

The mandatory Chromium gate uses a long host page and verifies fixed frame height, stable host document height, stable host scroll position, route changes, DOM churn, and repeated viewport resizing.
