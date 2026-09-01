# Site Intelligence v4.39.1 — Homepage Live Intelligence Asset Integrity & Rendering Recovery

## Why this patch exists

v4.39.0 introduced the new homepage Site Intelligence snapshot, but production diagnostics found a mixed-asset condition: the installed WordPress plugin reported v4.39.0 while its `sc-site-intelligence.js` and `sc-site-intelligence.css` bytes differed from the canonical v4.39.0 repository package. The backend, WordPress REST proxy, browser-style REST request, and Live Intelligence payload all remained healthy, while the homepage ticker displayed `LIVE INTELLIGENCE TEMPORARILY UNAVAILABLE`.

v4.39.1 repairs that release boundary and gives the frontend a new cache identity.

## Repair scope

- Bumps backend, WordPress plugin, release ID, public app assets, and runtime version references to **4.39.1**.
- Separates Live Intelligence **fetch failures** from **post-fetch rendering failures**.
- Adds per-signal rendering isolation so one malformed signal cannot collapse the complete ticker.
- Adds a bounded static display-recovery path when the normal renderer throws after a valid payload arrives.
- Removes the ticker dependency on `String.prototype.trimEnd()`.
- Converts homepage coverage cards to ordered metric slots rather than hard-coded metric IDs.
- Aligns the v4.39.1 homepage summary with capability counts: country profiles, enabled connectors, 35 public workspaces, and governed live ticker feeds.
- Adds SHA-256 asset manifests and repository-to-WordPress-ZIP byte-identity validation.

## Preserved capability

The patch does not roll back the v4.39.0 Live Intelligence gateway, rotation policy, evidence context, source lineage, Ocean, Space, country identity, or six-area / 35-route public architecture.

## Public endpoints

- `GET /public/live-intelligence/homepage`
- `GET /wp-json/sc-site-intelligence/v1/live-intelligence/homepage`
- `GET /v1/public/site-intelligence/summary`
- `GET /public/site-intelligence/summary`
- `GET /wp-json/sc-site-intelligence/v1/homepage-summary`

## WordPress shortcodes

```text
[sc_live_intelligence surface="homepage" limit="8" max_visible="8"]
[sc_site_intelligence_home]
```

## Release rule

A v4.39.1 WordPress package is invalid if its primary JS, CSS, or plugin PHP bytes differ from the corresponding repository source. The installer validates this before GitHub promotion.
