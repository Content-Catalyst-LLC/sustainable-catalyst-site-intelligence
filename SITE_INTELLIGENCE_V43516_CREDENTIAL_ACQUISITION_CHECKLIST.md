# v4.35.17 Credential Acquisition Checklist

Do not place credential values in Git, WordPress options, browser JavaScript, release bundles, screenshots, or support logs. Add them only as server-side environment variables in the deployment environment.

| Authority | Environment variable(s) | Acquisition requirement | Status in clean package |
|---|---|---|---|
| UN OCHA ReliefWeb | `SC_SI_RELIEFWEB_APPNAME` | Pre-approved ReliefWeb V2 appname | Missing |
| U.S. EPA AirNow | `SC_SI_AIRNOW_API_KEY` | AirNow account/API key | Missing |
| U.S. EPA AQS | `SC_SI_EPA_AQS_EMAIL`, `SC_SI_EPA_AQS_KEY` | Registered email and API key | Missing |
| U.S. EIA | `SC_SI_EIA_API_KEY` | EIA Open Data API key | Missing |
| Ember | `SC_SI_EMBER_API_KEY` | Ember Electricity Data API key | Missing |
| ENTSO-E | `SC_SI_ENTSOE_SECURITY_TOKEN` | Transparency Platform account and API security token | Missing |
| USDA NASS | `SC_SI_USDA_NASS_API_KEY` | NASS Quick Stats API key | Missing |
| NASA FIRMS | `SC_SI_NASA_FIRMS_MAP_KEY` | FIRMS MAP_KEY | Missing |
| HDX HAPI | `SC_SI_HDX_HAPI_APP_IDENTIFIER` | HDX HAPI application identifier | Missing |
| IPC | `SC_SI_IPC_API_KEY` | Approved IPC API access/key | Missing |
| Copernicus Marine | `SC_SI_COPERNICUS_MARINE_USERNAME`, `SC_SI_COPERNICUS_MARINE_PASSWORD` | Copernicus Marine account | Missing |
| Global Fishing Watch | `SC_SI_GLOBAL_FISHING_WATCH_API_TOKEN` | API v3 access token | Missing |

## After configuring a profile
1. Redeploy/restart the backend so environment settings are reloaded.
2. Check `/public/credential-configuration/readiness`.
3. Check `/public/credential-configuration/workspaces` to confirm the expected workspace moved to `configured`.
4. Exercise the specific connector with a bounded test request.
5. Confirm the provider's data remains semantically distinct from other evidence types.

The public readiness endpoint never validates credentials by transmitting them upstream. Provider authentication is confirmed only when the actual bounded connector request is exercised.
