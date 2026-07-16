# Site Intelligence v2.18.0 — Install and Test

## Install and push

Place the repository ZIP and installer directly in `~/Downloads`, then run:

```bash
cd ~/Downloads
chmod 700 install_and_push_site_intelligence_v2_18_0.sh
bash ./install_and_push_site_intelligence_v2_18_0.sh
```

The installer creates a safety archive and backup branch, resets the checkout to `origin/main`, applies the release, creates an isolated Python 3.13 environment, verifies FastAPI/Starlette/HTTPX2 TestClient compatibility, redirects every writable runtime path outside the repository, runs all 465 tests, validates release contracts and syntax, rechecks the immutable manifest, packages the WordPress plugin, commits, rebases, and pushes with GitHub CLI or SSH authentication. It does not request a GitHub username.

## Render deployment

After the push, open the Site Intelligence service in Render and choose **Manual Deploy → Clear build cache & deploy**.

Verify:

```bash
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/health | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/release | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/evidence-synthesis | python3 -m json.tool
```

All responses should report version `2.18.0`.

## WordPress deployment

Install `sustainable-catalyst-site-intelligence-v2.18.0-wordpress.zip` only after Render reports v2.18.0. Then open Site Intelligence release diagnostics and confirm backend/plugin parity.

New shortcodes:

- `[sc_public_evidence_synthesis]`
- `[sc_evidence_synthesis_control_center]` — administrators only

## Persistent state

Configure these paths on durable storage when claim and review records must survive redeployment:

- `SC_SI_EVIDENCE_SYNTHESIS_ROOT_PATH`
- `SC_SI_EVIDENCE_SYNTHESIS_CLAIMS_PATH`
- `SC_SI_EVIDENCE_SYNTHESIS_EVIDENCE_PATH`
- `SC_SI_EVIDENCE_SYNTHESIS_REVIEWS_PATH`
- `SC_SI_EVIDENCE_SYNTHESIS_SYNTHESES_PATH`
- `SC_SI_EVIDENCE_SYNTHESIS_UNCERTAINTY_PATH`

## Command-line checks

```bash
python3 scripts/evidence_synthesis_v2180.py summary
python3 scripts/evidence_synthesis_v2180.py methodology
python3 scripts/evidence_synthesis_v2180.py diagnostics
python3 scripts/validate_v2180_release.py
```
