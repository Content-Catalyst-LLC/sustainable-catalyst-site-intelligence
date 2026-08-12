# Site Intelligence v4.35.20 — Install & Test

## Install
Use the standalone macOS installer together with the matching v4.35.20 release bundle.

```bash
cd ~/Downloads

INSTALLER="$(find . -maxdepth 1 -type f \
  -name 'deploy_and_validate_site_intelligence_v4_35_18_macos*.sh' \
  -print0 | xargs -0 ls -t | head -1)"

BUNDLE="$(find . -maxdepth 1 -type f \
  -name 'sustainable-catalyst-site-intelligence-v4.35.20-release-bundle*.zip' \
  -print0 | xargs -0 ls -t | head -1)"

chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

## Bundle-only verification
```bash
SC_VERIFY_BUNDLE_ONLY=1 bash "$INSTALLER" "$BUNDLE"
```

## Repository verification
After extracting the repository ZIP:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
PYTHON=.venv/bin/python bash verify_site_intelligence_v4_35_18_macos.sh
SC_SI_SKIP_TESTS=1 SC_SI_RUN_BROWSER=1 PYTHON=.venv/bin/python bash verify_site_intelligence_v4_35_18_macos.sh
```

The second pass runs the 35-route browser audit across desktop, mobile, and iframe modes.
