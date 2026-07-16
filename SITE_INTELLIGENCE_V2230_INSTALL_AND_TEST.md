# Site Intelligence v2.23.0 Installation and Testing

## Install and push

```bash
cd ~/Downloads
chmod 700 install_and_push_site_intelligence_v2_23_0.sh
bash ./install_and_push_site_intelligence_v2_23_0.sh
```

The installer creates a safety archive and branch, resets the local repository to `origin/main`, applies the immutable release, creates an isolated Python environment, proves FastAPI TestClient and HTTPX2 compatibility, runs the full regression suite, validates syntax and release contracts, rechecks the manifest, packages the WordPress plugin, commits, rebases, and pushes through GitHub CLI or SSH without an interactive username prompt.

## Deploy

1. In Render, choose **Manual Deploy → Clear build cache & deploy**.
2. Verify `/health` and `/release` report `2.23.0`.
3. Verify `/public/cross-platform-workflows` and `/public/cross-platform-workflows/diagnostics`.
4. Install the WordPress ZIP only after backend parity is confirmed.

## WordPress shortcodes

- `[sc_public_cross_platform_workflows]`
- `[sc_cross_platform_workflows_control_center]`

The control center is administrator-only.

## Persistent state

Set the cross-platform workflow paths to a durable Render disk or another persistent filesystem before relying on packet, receipt, attempt, linkback, or recovery history across deployments.
