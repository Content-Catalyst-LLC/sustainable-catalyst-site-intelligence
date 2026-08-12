# Site Intelligence v4.35.22 — Credentials, API-Key & Configuration Completion

## Release purpose
v4.35.22 completes the configuration control plane for the platform's authenticated authoritative-source integrations. It does not manufacture, store, expose, or transmit credentials. Instead, it maps every current machine-readable AUTH_REQUIRED registration to one canonical server-side credential profile and exposes secret-safe readiness diagnostics.

## Credential control plane
- 17 authenticated machine-readable source registrations mapped.
- 12 deduplicated credential profiles.
- States: configured, missing, partial, invalid.
- Public responses expose environment-variable names and configuration state only.
- Secret values, masked values, hashes, fingerprints, last-four fragments, and lengths are never returned.
- Readiness performs no upstream network calls.
- Missing credentials remain non-blocking for deployment.

## New public routes
- `/public/credential-configuration`
- `/public/credential-configuration/readiness`
- `/public/credential-configuration/workspaces`

## Deployment configuration
Both Render blueprints and `backend/.env.example` now declare the complete canonical credential surface, including previously under-specified Copernicus Marine and Global Fishing Watch requirements and consistent EPA AQS declarations.

## Packaged configuration state
The release package contains no secrets. In a clean local environment the control plane reports 0 configured profiles and 12 missing profiles. Production state changes automatically as server-side environment variables are supplied.

## Release boundary
Credential completion is operational configuration, not release integrity. A valid Site Intelligence deployment must prove that the credential-control plane is mounted and deterministic, but a missing provider credential cannot turn a healthy deployment into a failed release.
