# Site Intelligence v3.22.5 Deployment Gate Audit

## Problem

Earlier builds could validate locally and update WordPress without proving that Render was serving the same backend commit. Even v3.22.4 relied on a one-time build-info poll and did not preserve a named rollback point.

## Repair

v3.22.5 introduces a durable release gate. Installation readiness requires the current backend version, a compatible WordPress version, an available Render branch and commit, the expected branch, the requested commit, and the production release channel.

The release identity is returned with `Cache-Control: no-cache, no-store, must-revalidate`, preventing a CDN or browser cache from presenting stale deployment metadata as current.

## Rollback readiness

Before synchronization, the promotion script records the branch head and creates an annotated tag named `site-intelligence-pre-v3.22.5-<commit>`. If deployment verification fails, the script prints the exact Render CLI command to deploy that prior commit. Rollback remains human-controlled.

## WordPress behavior

WordPress requests `/public/release-gate` with its plugin version, retains the legacy build-info endpoint contract, and records the gate state, Render commit, release fingerprint, and reason list. A healthy state is cached for 15 minutes; a mismatch is cached for only 45 seconds.
