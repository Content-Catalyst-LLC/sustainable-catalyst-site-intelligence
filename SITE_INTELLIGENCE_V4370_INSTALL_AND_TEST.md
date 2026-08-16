# Site Intelligence v4.37.0 — Install and Test

## Required deployment

1. Run `deploy_and_validate_site_intelligence_v4_37_0_macos.sh` from the release bundle.
2. The installer validates the immutable repository, runs the deterministic pytest suite and browser gates, pushes the certified tree to GitHub, creates tag `v4.37.0`, and waits for Render first-party verification.
3. Upload the bundled WordPress plugin ZIP and replace the existing Site Intelligence plugin.

## Optional ONC configuration

In the **Site Intelligence Render service**, add:

```text
SC_SI_ONC_API_TOKEN=<your Oceans 3.0 Web Services API token>
SC_SI_UNDERWATER_MEDIA_TIMEOUT_SECONDS=10
```

`SC_SI_ONC_API_TOKEN` is optional. If it is absent, ONC is shown as configuration-required while FathomNet and NOAA remain usable. Do not expose the token in WordPress or browser JavaScript.

## Production verification

```bash
BASE=https://sustainable-catalyst-site-intelligence.onrender.com
curl -fsS "$BASE/health" | python3 -m json.tool
curl -fsS "$BASE/public/underwater-media/providers" | python3 -m json.tool
curl -fsS "$BASE/public/underwater-media/readiness" | python3 -m json.tool
curl -fsS "$BASE/public/ocean-observation/readiness" | python3 -m json.tool
curl -fsS "$BASE/public/deployment-verification" | python3 -m json.tool
```

Expected first-party state: version `4.37.0`, underwater provider count `3`, FathomNet and NOAA public lanes ready, ONC missing credential non-blocking, Ocean system count `11`, and deployment verification `ok: true`.
