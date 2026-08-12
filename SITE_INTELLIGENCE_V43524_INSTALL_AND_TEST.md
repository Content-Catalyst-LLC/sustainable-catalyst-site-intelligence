# Site Intelligence v4.35.24 — Install & Test

## Recommended deployment

```bash
cd ~/Downloads
chmod +x deploy_and_validate_site_intelligence_v4_35_24_macos.sh
./deploy_and_validate_site_intelligence_v4_35_24_macos.sh \
  sustainable-catalyst-site-intelligence-v4.35.24-release-bundle.zip
```

## Palestine/Israel regression

From the repository root:

```bash
PYTHONPATH=backend:scripts python scripts/browser_palestine_navigation_integrity_v43524.py
```

The fixture intentionally provides hostile external identity metadata. Expected behavior is that `PSE` remains Palestine, `ISR` remains Israel, canonical map coordinates win, and cross-identity responses are blocked.

## Full browser gate

```bash
python scripts/browser_workspace_e2e_v43524.py --mode desktop
python scripts/browser_workspace_e2e_v43524.py --mode mobile
python scripts/browser_workspace_e2e_v43524.py --mode iframe
```

Expected result: 35/35 ready in each mode with zero degraded routes.

## First-party readiness

```text
/public/country-identity/readiness
/public/country-navigation-integrity/readiness
```

Both readiness checks are network-free. External country catalog health is intentionally non-blocking for release promotion.
