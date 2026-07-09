# Site Intelligence v1.0.1 — Public Shortcode Visual Alignment

This patch aligns the public Site Intelligence shortcode output with the current Sustainable Catalyst public-platform visual system.

## Recommended public page structure

Use the custom Site Intelligence page shell with these smaller public shortcodes:

```text
[sc_public_site_intelligence]
[sc_public_knowledge_overview]
[sc_public_climate_energy_summary]
[sc_public_methodology]
```

Do not nest `[sc_site_intelligence_public_flagship]` inside the custom page shell. The flagship shortcode remains available for a standalone all-in-one page only.

## Visual changes

- Public shortcode panels use cream/white backgrounds, black top rules, red uppercase labels, square-edged panels, and compact methodology-style rows.
- Public stat cards and source rows now match the newer Workbench / Methodology page language.
- Public modules embedded inside `.ccp-site-intelligence-public .ccp-live-shell` avoid the old nested rounded-card effect.

## Public boundary

The patch is visual only. It does not expose new analytics, credentials, private reports, or internal diagnostics.
