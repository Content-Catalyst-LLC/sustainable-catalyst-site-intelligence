# Site Intelligence v4.39.1 Asset Integrity & Browser Recovery Audit

## Production diagnosis carried forward

The production backend and WordPress proxy were verified independently before this patch. The failing state was isolated to the WordPress browser layer after the v4.39.0 upgrade.

The release fixes four boundaries:

1. **Asset identity** — a new release number prevents caches from treating divergent files as the same v4.39.0 asset.
2. **Failure classification** — a renderer exception no longer falls through the same promise rejection path used for network failure.
3. **Signal isolation** — each signal is rendered independently; a malformed browser-facing value can be skipped without suppressing all other valid signals.
4. **Homepage metric compatibility** — metric cards consume the ordered public payload rather than assuming one fixed set of metric IDs.

## Integrity controls

`WORDPRESS_ASSET_MANIFEST_V4391.json` records SHA-256 values for the canonical plugin PHP, main JS, and main CSS.

`scripts/validate_v4391_package_integrity.py` compares those repository files byte-for-byte with the packaged WordPress ZIP.

The macOS installer refuses promotion if source validation or package integrity fails.

## Browser recovery contract

When the public feed request succeeds but normal rendering throws, the component uses a bounded static representation of the returned signal label, value, and source. It marks delivery as `Display recovery`, not `Unavailable`.

Only a genuine request failure before a usable payload is obtained may produce `LIVE INTELLIGENCE TEMPORARILY UNAVAILABLE`.

## Truth boundaries

- The recovery renderer does not fabricate replacement signals.
- It does not alter source observations, freshness, evidence, or selection order.
- It does not bypass backend validation or expiry suppression.
- It does not expose private state or credentials.

## Inherited mirror defects closed during certification

The full suite found six pre-existing files whose backend public-app and WordPress mirrors were not byte-identical: `app.js`, `browser-reliability-v3235.css`, `cartographic-workspace-v3230.js`, `orbital-earth-v4100.js`, `science-v240.js`, and `world-cartography-v3229.geojson`. v4.39.1 normalizes all six to the backend public-app copies and the release validator now checks every same-named browser mirror.

The suite also exposed an unrelated but real public supply-chain diagnostic defect in `security_observability_assurance_v3310.py`: the supply-chain endpoint referenced an undefined repository `ROOT`. v4.39.1 defines that root explicitly so the diagnostic remains callable.
