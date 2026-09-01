# Site Intelligence v4.39.0 R2 — Install and Test

## Deployment order

1. Run the Mac installer to validate, commit, tag `v4.39.0-r2`, and push the release to GitHub.
2. Pull `main` on the VPS and rebuild the `site-intelligence` Compose service.
3. Replace the WordPress plugin with the R2 plugin ZIP.
4. Replace the homepage source with `sustainable-catalyst-homepage-v4.3.1.html`.
5. Clear page, object, CDN, and browser caches.

## Expected homepage metrics

- 172 country profiles
- 14 enabled connectors
- 35 public workspaces
- 8 live ticker feeds

These counts describe different registries. They must not be added together or interpreted as a count of simultaneous real-time observations.

## Visual checks

- No generic tan section surrounds the black Site Intelligence console.
- Earth, Space, and Ocean imagery remains visible in a shorter visual panel.
- The original green ticker scrolls inside the console and retains pause behavior.
- Metric, signal, entry-point, and footer cards use less vertical space.
- The `Featured now` count matches the bounded highlight response.

## Health checks

- `/health` returns HTTP 200 and version `4.39.0`.
- `/v1/public/site-intelligence/summary` returns the four expected capability metrics.
- The WordPress admin diagnostic summary reports backend and plugin version `4.39.0` with the release gate ready.
