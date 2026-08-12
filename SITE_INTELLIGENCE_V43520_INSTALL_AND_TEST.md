# Site Intelligence v4.35.22 — Install & Test

## Install
Use the standalone macOS installer with the matching v4.35.22 release bundle.

```bash
cd ~/Downloads

chmod +x deploy_and_validate_site_intelligence_v4_35_20_macos.sh

./deploy_and_validate_site_intelligence_v4_35_20_macos.sh \
  sustainable-catalyst-site-intelligence-v4.35.22-release-bundle.zip
```

## Bundle-only verification
```bash
SC_VERIFY_BUNDLE_ONLY=1 bash \
  deploy_and_validate_site_intelligence_v4_35_20_macos.sh \
  sustainable-catalyst-site-intelligence-v4.35.22-release-bundle.zip
```

## Repository verification
After extracting the repository ZIP:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
PYTHON=.venv/bin/python bash verify_site_intelligence_v4_35_20_macos.sh
SC_SI_SKIP_TESTS=1 SC_SI_RUN_BROWSER=1 PYTHON=.venv/bin/python \
  bash verify_site_intelligence_v4_35_20_macos.sh
```

The browser pass verifies the inherited 35-route workspace across desktop, mobile, and iframe modes. The release verifier also requires the network-free country-linked record readiness contract while keeping external provider health non-blocking.
