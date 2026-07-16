# Site Intelligence v2.17.0 — Install and Test

## Install and push

Place the repository ZIP and installer directly in `~/Downloads`, then run:

```bash
cd ~/Downloads
chmod 700 install_and_push_site_intelligence_v2_17_0.sh
bash ./install_and_push_site_intelligence_v2_17_0.sh
```

The installer creates a safety archive and backup branch, resets the local checkout to `origin/main`, applies the release, creates an isolated Python 3.13 validation environment, explicitly verifies FastAPI/Starlette/HTTPX2 TestClient compatibility, redirects all writable runtime state outside the repository, runs the complete backend suite, validates release contracts and syntax, verifies the immutable manifest after testing, packages the WordPress plugin, commits, rebases, and pushes with GitHub CLI or SSH authentication. It will not prompt for a GitHub username.

## Render deployment

After the push, open the Site Intelligence service in Render and choose **Manual Deploy → Clear build cache & deploy**. Confirm the deployment uses the new commit.

Verify:

```bash
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/health | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/release | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/model-governance | python3 -m json.tool
```

All responses should report version `2.17.0`.

## WordPress deployment

Install `sustainable-catalyst-site-intelligence-v2.17.0-wordpress.zip` only after Render reports v2.17.0. Then open Site Intelligence release diagnostics and confirm backend/plugin parity.

New shortcodes:

- `[sc_public_model_forecasts]`
- `[sc_model_forecast_control_center]` — administrators only

## Persistent state

The default model-governance directory is file-backed. Configure these paths on durable storage for production persistence:

- `SC_SI_MODEL_GOVERNANCE_ROOT_PATH`
- `SC_SI_MODEL_GOVERNANCE_MODELS_PATH`
- `SC_SI_MODEL_GOVERNANCE_FORECASTS_PATH`
- `SC_SI_MODEL_GOVERNANCE_EVALUATIONS_PATH`
- `SC_SI_MODEL_GOVERNANCE_WARNING_RULES_PATH`
- `SC_SI_MODEL_GOVERNANCE_WARNING_EVENTS_PATH`

## Command-line checks

```bash
python3 scripts/model_governance_v2170.py summary
python3 scripts/model_governance_v2170.py methodology
python3 scripts/model_governance_v2170.py diagnostics
python3 scripts/validate_v2170_release.py
```
