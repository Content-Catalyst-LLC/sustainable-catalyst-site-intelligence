# Site Intelligence v4.39.2 — Live Intelligence Frontend Recovery

v4.39.2 is a forward repair release built directly from the restored v4.39.0 production baseline. It repairs the homepage Live Intelligence browser rendering path without redesigning or replacing the approved Site Intelligence homepage experience.

## Repair

- Separates successful feed delivery from frontend rendering failure so a renderer exception is no longer mislabeled as a backend outage.
- Isolates individual signal rendering failures instead of allowing one malformed signal to take down the entire ticker.
- Adds a bounded minimal display fallback using the already-returned public signal payload when rich rendering fails.
- Preserves the existing network-failure state for genuine REST/proxy failures.
- Advances the WordPress and backend semantic release identity to `4.39.2` so the production release gate remains matched.
- Updates only the top-level release-version metadata in governed backend policy JSON files required for a valid `4.39.2` backend boot.

## Explicit preservation boundary

This release does **not** redesign Site Intelligence.

- The `[sc_site_intelligence_home]` shortcode body is byte-for-byte identical to v4.39.0.
- The Site Intelligence CSS is byte-for-byte identical to v4.39.0.
- Explore the World, Earth & Environment, and Ocean & Space entry points are unchanged.
- The external WordPress homepage composition, including the approved Earth / Space / Ocean triptych, is not modified by this package or installer.
- All backend application logic is unchanged except the central semantic version identity.
- Governed policy files change only their top-level `version` value from `4.39.0` to `4.39.2`.
- The only functional frontend code change is inside `setupLiveIntelligence()` in `sc-site-intelligence.js`.

## Deployment identity

After both sides are deployed:

```text
WordPress plugin: 4.39.2
Backend:          4.39.2
Release gate:     matched
```

The main browser asset will be cache-busted as `sc-site-intelligence.js?ver=4.39.2`.
