# Site Intelligence v3.1.4 — Readability and Taxonomy Controls

## Purpose

This release improves the electronic Live Intelligence board without changing its source-selection, placement, cache, or theme-surface behavior.

## Readability controls

- Relaxed: 42 seconds desktop / 48 seconds mobile
- Balanced: 30 seconds desktop / 36 seconds mobile
- Brisk: 24 seconds desktop / 30 seconds mobile
- Custom desktop and mobile cycle durations
- Compact, balanced, and spacious signal spacing
- Configurable 48–220 character signal-text limit
- Ellipsis treatment for long labels and values
- Compact source-name display using source-provided short names

Hover, keyboard focus, the pause button, and reduced-motion preferences continue to stop movement.

## Taxonomy controls

Administrators can edit display labels for:

- `earth_systems`
- `human_systems`
- `research`
- `economy_resources`
- `platform`

The default `economy_resources` label is **Economy, Energy & Resources**. Canonical IDs, filters, APIs, saved feed selections, and shortcode category values do not change.

## Administration

The settings page includes a visual preview that updates with speed, spacing, text-length, compact-source, and taxonomy controls without making external API requests. A separate restore action resets only readability and taxonomy settings while preserving feeds, placement, scope, backend, and theme choices.

## Boundaries

- No Astra navigation or breadcrumb colors are changed.
- No source is enabled or disabled by a readability setting.
- Shortened display text does not alter the stored source record.
- Full signal context remains available through accessible labels, titles, and destination links.
