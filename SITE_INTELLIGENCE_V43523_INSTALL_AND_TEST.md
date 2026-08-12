# Site Intelligence v4.35.23 — Install & Test

## Recommended deployment

From `~/Downloads`:

```bash
cd ~/Downloads
chmod +x deploy_and_validate_site_intelligence_v4_35_23_macos.sh
./deploy_and_validate_site_intelligence_v4_35_23_macos.sh \
  sustainable-catalyst-site-intelligence-v4.35.23-release-bundle.zip
```

## Deterministic validation

The verifier checks release identity, static contracts, the complete pytest suite, immutable manifest integrity, JavaScript/PHP/static security validation, and—when browser verification is enabled—the 35-route desktop/mobile/iframe gate.

The dedicated country-identity browser regression can be run from the repository root with:

```bash
PYTHONPATH=backend:scripts python scripts/browser_country_identity_routing_v43523.py
```

Expected behavior:

- selecting Israel leaves `#countrySelect`, identity code, profile name, title and route state on `ISR / Israel`;
- selecting Palestine leaves them on `PSE / Palestine`;
- rapid switching resolves to the last selected ISO3;
- no response with a mismatched ISO3 is rendered.

## First-party readiness route

```text
/public/country-identity/readiness
```

This readiness check is network-free. External country catalogs are enrichment-only and do not block release promotion.
