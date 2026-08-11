# Site Intelligence v4.35.1 — Install and Test

1. In Render, set `SC_SI_PLATFORM_CORE_URL` to the deployed Sustainable Catalyst Platform Core backend URL. The release blueprint sets `SC_SI_PLATFORM_CORE_ENABLED=true`. Add `SC_SI_PLATFORM_CORE_PUBLIC_API_KEY` only if that Core deployment requires authenticated public reads.
2. Put the v4.35.1 release bundle and deploy script in `~/Downloads`.
3. Run:

```bash
cd ~/Downloads
chmod +x deploy_and_validate_site_intelligence_v4_35_1_macos.sh
./deploy_and_validate_site_intelligence_v4_35_1_macos.sh
```

The installer verifies checksums, creates an isolated Python environment, runs the deterministic repository test suite, runs the browser/static gate, promotes the backend through GitHub/Render, and leaves the WordPress plugin ZIP in the extracted deployment folder.

After deployment, verify:

- `/public/v4/configuration-readiness` reports `platform_core.public_read_configured: true` and `core_required_routes_unavailable: []`.
- `/public/countries/search?q=Palestine` returns `PSE` with display name `Palestine`.
- `/public/country/PSE`, `/public/country/PS`, and the accepted Palestine aliases resolve to the same country identity.
