# Site Intelligence v4.34.0 — Install and Test

## Required order

1. Run the macOS installer against the v4.34.0 release bundle.
2. Allow deterministic repository validation to finish.
3. Allow GitHub promotion and bounded Render verification to finish.
4. Confirm the live release gate reports exact v4.34.0 version, release id and expected commit.
5. Only then install the WordPress ZIP.

## Release package files

- `sustainable-catalyst-site-intelligence-v4.34.0-repository.zip`
- `sustainable-catalyst-site-intelligence-v4.34.0-wordpress-plugin.zip`
- `deploy_and_validate_site_intelligence_v4_33_0_macos.sh`
- `SHA256SUMS.txt`

## Deterministic verifier

The v4.33 verifier validates:

- backend and WordPress version synchronization;
- inherited public endpoint contracts plus new v4.33 contracts;
- exact mirrored Earth-environment JS/CSS assets;
- immutable manifest hashes with no `backend/backend/` runtime state;
- JSON/GeoJSON parsing;
- JavaScript syntax;
- WordPress PHP syntax;
- static security scan;
- all collected pytest tests, executed in deterministic test-file chunks;
- optional direct/iframe-compatible v4.33 browser contract.

## Bundle-only validation

To verify the bundle without GitHub/Render promotion:

```bash
SC_VERIFY_BUNDLE_ONLY=1 bash deploy_and_validate_site_intelligence_v4_33_0_macos.sh sustainable-catalyst-site-intelligence-v4.34.0-release-bundle.zip
```
