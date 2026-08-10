# Site Intelligence v4.17.0 — Install and Test

1. Put `deploy_and_validate_site_intelligence_v4_17_0_macos.sh` and the v4.17.0 release bundle in `~/Downloads`.
2. Run the installer with the release bundle as its argument.
3. The installer verifies bundle SHA-256 values, extracts the immutable repository, creates an isolated Python environment, runs deterministic validation pass 1, runs static/package pass 2, then promotes GitHub/Render.
4. Do not install the WordPress ZIP until the terminal reports the exact v4.17.0 live release gate passed.

The verifier rejects `backend/backend/` nested runtime state and checks the immutable manifest before and after the full regression suite.
