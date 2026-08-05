# Site Intelligence v3.22.6 installation and deployment

Use the deployment installer included with the release bundle. It performs local validation, promotes the exact release tree to `Content-Catalyst-LLC/sustainable-catalyst-site-intelligence`, pushes the release tag, and verifies the live Render backend before exposing the WordPress ZIP for installation.

## Standard terminal command

```bash
cd ~/Downloads
chmod +x deploy_and_validate_site_intelligence_v3_22_4_macos.sh
bash deploy_and_validate_site_intelligence_v3_22_4_macos.sh \
  sustainable-catalyst-site-intelligence-v3.22.6-release-bundle.zip
```

## Optional Render controls

The normal path relies on Render auto-deploy from the connected Git branch. For deterministic triggering, define one of these before running the installer:

```bash
export SC_SI_RENDER_DEPLOY_HOOK='YOUR_SECRET_RENDER_DEPLOY_HOOK_URL'
```

or authenticate the Render CLI. The script then runs a clear-cache deploy for the pushed commit.

## Live verification

```bash
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/build-info | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/deployment-status | python3 -m json.tool
```

Do not install the WordPress ZIP until both endpoints report v3.22.6 and the Git commit printed by the deployment script.
