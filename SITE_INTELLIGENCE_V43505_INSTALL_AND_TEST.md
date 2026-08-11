# Site Intelligence v4.35.5 — Install and Test

Deploy the release bundle with the supplied macOS installer. The installer verifies SHA-256 checksums, creates an isolated Python environment, runs the deterministic verifier twice, pushes the backend to GitHub/Render, and verifies first-party deployment identity without treating upstream source health as a release blocker.

## Required only for gated Expansion III connectors

Set these as secret Render environment variables if you want the corresponding connectors to become operational:

```text
SC_SI_NASA_FIRMS_MAP_KEY=<free FIRMS map key>
SC_SI_USDA_NASS_API_KEY=<NASS Quick Stats API key>
```

Optional for authorized NASA CMR concepts:

```text
SC_SI_NASA_EARTHDATA_TOKEN=<Earthdata bearer token>
```

NWI, EPA ECHO, and public CMR GraphQL metadata discovery require no credential. Absence of FIRMS/NASS credentials is reported as configuration-required and does not fail deployment.
