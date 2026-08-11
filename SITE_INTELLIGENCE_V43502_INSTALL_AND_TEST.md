# Site Intelligence v4.35.2 — Install and Test

1. Place the v4.35.2 release bundle and deploy script in `~/Downloads`.
2. In Render, preserve the v4.35.1 Platform Core settings. For live ReliefWeb humanitarian reports, add a pre-approved ReliefWeb V2 appname as `SC_SI_RELIEFWEB_APPNAME`.
3. Run:

```bash
cd ~/Downloads
chmod +x deploy_and_validate_site_intelligence_v4_35_2_macos.sh
./deploy_and_validate_site_intelligence_v4_35_2_macos.sh
```

The installer verifies bundle checksums, creates an isolated virtual environment, runs deterministic validation, runs the browser/static reliability gate, promotes the backend through GitHub/Render, and verifies the live release contract.

After deployment, inspect **Sources & Methodology → Authoritative API Coverage**. A registered source must not be described as LIVE unless a retrieval path is implemented and its required configuration is present.
