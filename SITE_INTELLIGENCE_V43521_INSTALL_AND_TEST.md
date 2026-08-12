# Site Intelligence v4.35.21 — Install & Test

## Install
Use the standalone macOS installer with the matching v4.35.21 release bundle.

```bash
cd ~/Downloads
chmod +x deploy_and_validate_site_intelligence_v4_35_21_macos.sh
./deploy_and_validate_site_intelligence_v4_35_21_macos.sh \
  sustainable-catalyst-site-intelligence-v4.35.21-release-bundle.zip
```

## Bundle-only verification
```bash
SC_VERIFY_BUNDLE_ONLY=1 bash \
  deploy_and_validate_site_intelligence_v4_35_21_macos.sh \
  sustainable-catalyst-site-intelligence-v4.35.21-release-bundle.zip
```

## Repository verification
After extracting the repository ZIP:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
PYTHON=.venv/bin/python bash verify_site_intelligence_v4_35_21_macos.sh
SC_SI_SKIP_TESTS=1 SC_SI_RUN_BROWSER=1 PYTHON=.venv/bin/python \
  bash verify_site_intelligence_v4_35_21_macos.sh
```

The deterministic verifier expects **1,629 collected tests**. Browser verification runs the 35-route workspace independently in desktop, mobile, and iframe modes. Palestine Data Federation and Wikimedia Knowledge Context readiness are first-party/network-free gates; live external source health remains non-blocking.
