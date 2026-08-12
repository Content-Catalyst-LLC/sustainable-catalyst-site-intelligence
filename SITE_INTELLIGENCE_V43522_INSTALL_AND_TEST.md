# Site Intelligence v4.35.22 — Install & Test

## Install
```bash
cd ~/Downloads
chmod +x deploy_and_validate_site_intelligence_v4_35_22_macos.sh
./deploy_and_validate_site_intelligence_v4_35_22_macos.sh \
  sustainable-catalyst-site-intelligence-v4.35.22-release-bundle.zip
```

## Bundle-only verification
```bash
SC_VERIFY_BUNDLE_ONLY=1 bash \
  deploy_and_validate_site_intelligence_v4_35_22_macos.sh \
  sustainable-catalyst-site-intelligence-v4.35.22-release-bundle.zip
```

## Repository verification
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
PYTHON=.venv/bin/python bash verify_site_intelligence_v4_35_22_macos.sh
SC_SI_SKIP_TESTS=1 SC_SI_RUN_BROWSER=1 PYTHON=.venv/bin/python \
  bash verify_site_intelligence_v4_35_22_macos.sh
```

The deterministic verifier checks the complete inherited suite plus the v4.35.22 reconciliation/scope regressions. Browser verification keeps the 35-route desktop/mobile/iframe gate. External provider health remains non-blocking.
