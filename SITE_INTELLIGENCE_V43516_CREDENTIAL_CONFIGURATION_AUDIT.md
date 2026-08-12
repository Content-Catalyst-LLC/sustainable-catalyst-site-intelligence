# Site Intelligence v4.35.21 — Credential Configuration Audit

## Audit conclusion
All 17 machine-readable `AUTH_REQUIRED` source registrations are mapped to 12 canonical credential profiles. The control plane is deterministic, secret-safe, network-free, and non-blocking for release promotion.

## Canonical profiles
| Profile | Authority | Required environment | Registry rows |
|---|---|---|---:|
| ReliefWeb appname | UN OCHA ReliefWeb | `SC_SI_RELIEFWEB_APPNAME` | 3 |
| AirNow API key | U.S. EPA AirNow | `SC_SI_AIRNOW_API_KEY` | 1 |
| EPA AQS | U.S. EPA Air Quality System | `SC_SI_EPA_AQS_EMAIL`, `SC_SI_EPA_AQS_KEY` | 2 |
| EIA API key | U.S. Energy Information Administration | `SC_SI_EIA_API_KEY` | 2 |
| Ember API key | Ember | `SC_SI_EMBER_API_KEY` | 1 |
| ENTSO-E token | ENTSO-E | `SC_SI_ENTSOE_SECURITY_TOKEN` | 1 |
| USDA NASS key | USDA NASS | `SC_SI_USDA_NASS_API_KEY` | 1 |
| NASA FIRMS MAP_KEY | NASA LANCE FIRMS | `SC_SI_NASA_FIRMS_MAP_KEY` | 1 |
| HDX HAPI identifier | OCHA/HDX HAPI | `SC_SI_HDX_HAPI_APP_IDENTIFIER` | 1 |
| IPC API key | Integrated Food Security Phase Classification | `SC_SI_IPC_API_KEY` | 1 |
| Copernicus Marine account | Copernicus Marine Service | `SC_SI_COPERNICUS_MARINE_USERNAME`, `SC_SI_COPERNICUS_MARINE_PASSWORD` | 2 |
| Global Fishing Watch token | Global Fishing Watch | `SC_SI_GLOBAL_FISHING_WATCH_API_TOKEN` | 1 |

## Packaged-state result
A clean release environment intentionally contains no provider secrets:
- configured: 0
- missing: 12
- partial: 0
- invalid: 0
- configuration_complete: false
- completion_status: not-configured

This is expected package behavior, not a release failure.

## Security properties
1. Public credential diagnostics return configuration state and canonical environment names only.
2. Secret values are never returned.
3. Secret hashes, masks, fingerprints, lengths, or suffixes are never returned.
4. Readiness makes no provider network requests.
5. Credentials remain server-side environment configuration.
6. Missing credentials are operational source-health/configuration conditions, not deployment blockers.

## Configuration debt repaired
v4.35.21 adds canonical settings and deployment declarations for Copernicus Marine and Global Fishing Watch and aligns EPA AQS declarations across the root and backend Render blueprints. `backend/.env.example` now documents the complete environment-variable surface.
