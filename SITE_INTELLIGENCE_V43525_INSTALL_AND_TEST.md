# Site Intelligence v4.35.25 — Install & Test

## Recommended deployment

```bash
cd ~/Downloads
chmod +x deploy_and_validate_site_intelligence_v4_35_25_macos.sh
./deploy_and_validate_site_intelligence_v4_35_25_macos.sh \
  sustainable-catalyst-site-intelligence-v4.35.25-release-bundle.zip
```

## Country presentation contract

```bash
PYTHONPATH=backend python scripts/validate_v43525_release_contract.py
PYTHONPATH=backend python -m pytest -q backend/tests/test_country_evidence_presentation_v43525.py
```

Expected behavior includes:

- World Bank annual electricity access is labeled as a harmonized structural benchmark.
- Structural electricity/water indicators explicitly state that they do not establish current service availability.
- Conditions Now remains separate from annual/structural statistics.
- Palestine source authority guidance identifies PCBS as preferred for compatible official statistical concepts.

## Country navigation regression

```bash
PYTHONPATH=backend:scripts python scripts/browser_palestine_navigation_integrity_v43525.py
```

## Country presentation browser regression

```bash
PYTHONPATH=backend:scripts python scripts/browser_country_evidence_presentation_v43525.py
```

## Full browser gate

```bash
python scripts/browser_workspace_e2e_v43525.py --mode desktop
python scripts/browser_workspace_e2e_v43525.py --mode mobile
python scripts/browser_workspace_e2e_v43525.py --mode iframe
```

## First-party readiness

```text
/public/country-evidence-presentation/readiness
/public/country-navigation-integrity/readiness
/public/country-identity/readiness
/public/country-evidence-reconciliation/readiness
```

These readiness surfaces are network-free; external provider health remains non-blocking for release promotion.
