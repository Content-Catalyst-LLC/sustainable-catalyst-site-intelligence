# Site Intelligence v1.12.6 — Live Data Rendering and Public Dashboard Repair

This release repairs the public rendering path for Public Intelligence Dashboard, Country Intelligence, and Cross-Domain Comparison.

## Principles

- Show validated connector values only.
- Never invent or silently impute a precise value.
- Keep source-registry and methodology context visible when live values are unavailable.
- Label backend, cached, stale, and WordPress-local-fallback states explicitly.
- Render dashboard, country, and comparison payloads with schema-specific components rather than generic connector cards.

## Diagnostic endpoint

`/public/dashboard-studio/rendering-diagnostics`
