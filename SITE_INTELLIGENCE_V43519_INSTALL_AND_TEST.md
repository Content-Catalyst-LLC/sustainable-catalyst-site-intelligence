# Site Intelligence v4.35.22 — Install & Test

## Install
Use the standalone macOS installer together with the matching v4.35.22 release bundle.

```bash
cd ~/Downloads

INSTALLER="$(find . -maxdepth 1 -type f \
  -name 'deploy_and_validate_site_intelligence_v4_35_19_macos*.sh' \
  -print0 | xargs -0 ls -t | head -1)"

BUNDLE="$(find . -maxdepth 1 -type f \
  -name 'sustainable-catalyst-site-intelligence-v4.35.22-release-bundle*.zip' \
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
PYTHON=.venv/bin/python bash verify_site_intelligence_v4_35_19_macos.sh
SC_SI_SKIP_TESTS=1 SC_SI_RUN_BROWSER=1 PYTHON=.venv/bin/python bash verify_site_intelligence_v4_35_19_macos.sh
```

The deterministic pass verifies the v4.35.22 soak/semantic release contract and complete pytest suite. The browser pass preserves the 35-route desktop/mobile/iframe reliability gate.
