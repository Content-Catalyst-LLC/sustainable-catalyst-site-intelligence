# Site Intelligence v4.39.2 — Preservation Audit

Baseline: `v4.39.0`
Target: `v4.39.2`

## Certified runtime scope

The release validator compares the v4.39.2 tree against a retained v4.39.0 hash baseline.

- 842 non-target backend and WordPress runtime files: byte-for-byte identical.
- 27 governed backend policy JSON files: only the top-level `version` value changes from `4.39.0` to `4.39.2`.
- `backend/app/version.py`: only `APP_VERSION` changes from `4.39.0` to `4.39.2`.
- WordPress plugin bootstrap: only plugin header version, `VERSION`, and `RELEASE_ID` change.
- `sc-site-intelligence.js`: changes are confined to `setupLiveIntelligence()`.
- Main Site Intelligence CSS SHA-256 remains `d421bb06da51d26b83be1c0f5309e7aa16f7dd927a8868da6505f80f7c758db1`.
- `[sc_site_intelligence_home]` shortcode-body SHA-256 remains `3a826ffc97127dd4ccb415ddbc12c650aabcf7901d3c7f46bbf0d5faa8b8a744`.

## Homepage preservation

The following approved Site Intelligence homepage entry structure remains present and unchanged:

- Explore the World
- Earth & Environment
- Ocean & Space
- coverage metrics
- bounded public signals
- Site Intelligence CTA

The WordPress page content that contains the Earth / Space / Ocean triptych is outside this plugin repository and is not touched by the v4.39.2 installer.

## Live Intelligence repair boundary

The renderer now:

1. treats HTTP/REST failure as a feed-load failure;
2. treats a JavaScript exception after successful JSON delivery as a display failure;
3. attempts per-signal safe rendering;
4. falls back to a minimal signal strip from the same returned payload if rich rendering fails;
5. retains the existing unavailable state only when the request itself fails.
