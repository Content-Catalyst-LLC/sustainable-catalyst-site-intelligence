# Install and Test Site Intelligence v3.22.6

1. Place the release bundle and `deploy_and_validate_site_intelligence_v3_22_5_macos.sh` in `~/Downloads`.
2. Run the terminal command supplied with the release.
3. The installer verifies checksums, creates an isolated Python environment, runs the complete suite, pushes GitHub, triggers Render, and polls the live release gate.
4. Install the WordPress ZIP only after the terminal reports that the gate is ready.
5. In WordPress, open **Settings → SC Site Intelligence** and confirm:
   - State: `match`
   - Gate: `ready`
   - Backend: `3.22.6`
   - Commit: the same first 12 characters printed by Terminal
6. Purge WordPress, hosting, CDN, and browser caches.

## Manual live check

```bash
curl -fsS "https://sustainable-catalyst-site-intelligence.onrender.com/public/release-gate?plugin_version=3.22.6"
```

The JSON response should report `"install_allowed": true` and `"gate_state": "ready"`.
