# Site Intelligence v4.39.0 — Homepage Live Intelligence Snapshot

## Outcome

The homepage can now demonstrate Site Intelligence as a functioning public platform without embedding the full application.

Use:

```text
[sc_site_intelligence_home]
```

The component loads a small summary payload, presents registry-derived coverage metrics, shows up to four current source-linked signals, and provides three focused entry points plus the main application action.

## Public API

- `GET /v1/public/site-intelligence/summary`
- Compatibility alias: `GET /public/site-intelligence/summary`
- WordPress proxy: `GET /wp-json/sc-site-intelligence/v1/homepage-summary`

The response is bounded and public-safe. It contains no API tokens, private analytics, visitor profiles, administrative state, or fabricated fallback records.

## Degraded behavior

If upstream live sources are unavailable, the backend returns registry counts with zero live highlights. If the homepage request itself fails, WordPress displays an explicit unavailable state, leaves metric values blank, and preserves direct navigation.

## Inherited capability

v4.39.0 retains the v4.38.0 Live Space and iframe repairs, the eleven-system Ocean workspace, first-party country identity, evidence hierarchy, and the six-area / 35-route public architecture.
