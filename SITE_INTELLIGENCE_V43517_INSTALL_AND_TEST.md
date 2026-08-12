# Site Intelligence v4.35.21 — Install & Test

## Install
Use the release bundle and the standalone macOS installer generated with this release.

```bash
cd ~/Downloads
chmod +x deploy_and_validate_site_intelligence_v4_35_17_macos.sh
./deploy_and_validate_site_intelligence_v4_35_17_macos.sh sustainable-catalyst-site-intelligence-v4.35.21-release-bundle.zip
```

## Expected deterministic result
The release verifier collects and runs 1,595 deterministic pytest tests in bounded file chunks, then performs manifest, JSON/GeoJSON, JavaScript, PHP, security, and browser/static resilience gates.

## Production smoke checks
After Render is at v4.35.21, verify:
- `/public/external-resilience/readiness` returns `ok=true`, `network_calls_performed=false`.
- `/public/deployment-verification` includes `external_resilience_control_plane_ready=true`.
- `/public/source-health-policy` exposes an `external_resilience` summary with upstream health non-blocking.
- `/app/?view=sources` shows the External Resilience panel.

Do not expect provider telemetry to be populated until live connector requests occur on that process.
