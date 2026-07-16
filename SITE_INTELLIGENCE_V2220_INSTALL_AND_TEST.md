# Site Intelligence v2.22.0 — Install and Test

## Install

Place the repository ZIP and installer in `~/Downloads`, then run:

```bash
cd ~/Downloads
chmod 700 install_and_push_site_intelligence_v2_22_0.sh
bash ./install_and_push_site_intelligence_v2_22_0.sh
```

The installer creates a safety archive and branch, resets the local checkout to `origin/main`, installs the immutable release overlay, creates an isolated Python environment, proves FastAPI TestClient compatibility, runs the full regression suite, validates release contracts and syntax, rechecks the immutable manifest, creates the WordPress plugin ZIP, commits, rebases, and pushes using GitHub CLI or SSH without an interactive username prompt.

## Deploy

In Render, select **Manual Deploy → Clear build cache & deploy**. Confirm `/health` and `/release` report `2.22.0` before installing the WordPress plugin.

## Verify

```bash
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/health | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/release | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/institutional-workspaces | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/institutional-workspaces/diagnostics | python3 -m json.tool
```

## Persistence

Set every `SC_SI_INSTITUTIONAL_WORKSPACES_*_PATH` to a durable mounted path in production. The default repository-relative paths are suitable for local development but will not survive replacement of an ephemeral Render instance.

## WordPress

Install `sustainable-catalyst-site-intelligence-v2.22.0-wordpress.zip` only after backend parity is confirmed.

Shortcodes:

- `[sc_public_institutional_workspaces]`
- `[sc_institutional_workspace workspace_id="workspace-id"]`
- `[sc_institutional_workspaces_control_center]`
