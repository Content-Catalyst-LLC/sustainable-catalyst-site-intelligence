# Site Intelligence v4.35.20 — Install & Test

## Install
Run the standalone macOS installer with the v4.35.20 release bundle. The installer verifies bundle checksums, validates the repository, runs deterministic tests, synchronizes GitHub, and verifies the Render release receipt when promotion is enabled.

## Local validation
```bash
PYTHONPATH=backend python -m pytest -q backend/tests/test_credentials_api_key_configuration_completion_v43516.py
PYTHONPATH=backend python scripts/validate_v43516_release_contract.py
SC_SI_SKIP_TESTS=1 SC_SI_RUN_BROWSER=1 PYTHON=python bash verify_site_intelligence_v4_35_16_macos.sh
```

## Credential diagnostics
```bash
curl -fsS https://YOUR-BACKEND/public/credential-configuration/readiness
curl -fsS https://YOUR-BACKEND/public/credential-configuration/workspaces
```

A clean package should report the credential control plane as `ok=true` even when `configuration_complete=false`. Missing credentials do not block release promotion.

## Secret handling
Never paste provider credentials into public URLs, browser code, WordPress content, Git commits, diagnostic exports, or release artifacts. Configure them only as server-side environment variables.
