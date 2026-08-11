# Site Intelligence v4.35.1 — Country Resolution, Workspace Availability & Configuration Repair

## Purpose

This reliability patch repairs two production-truth problems identified after v4.35.1: country resolution for Palestine and hidden runtime configuration dependencies that made registered workspaces appear unavailable.

## Country resolution

- Canonical display: **Palestine**
- ISO3: `PSE`
- ISO2: `PS`
- Accepted aliases resolve to the same `PSE` workspace: `Palestine`, `State of Palestine`, `Palestinian Territories`, `Palestinian Territory`, and `West Bank and Gaza`.
- `PSE` is present in the offline fallback country catalog, so the selector does not lose Palestine when the World Bank catalog is temporarily unreachable.

## Workspace availability and configuration

The route directory was already structurally complete. The actual missing dependency was the Platform Core public-read bridge used by the Economics, International Law, Scientific Earth Systems, and Trade/Energy/Resources workspaces. v4.35.1 adds runtime diagnostics to `/public/v4/readiness` and the dedicated `/public/v4/configuration-readiness` endpoint. No credentials or secret values are returned.

For full record availability set in the Render service environment:

```text
SC_SI_PLATFORM_CORE_ENABLED=true
SC_SI_PLATFORM_CORE_URL=https://YOUR-CORE-SERVICE.onrender.com
```

Optional only when applicable:

```text
SC_SI_PLATFORM_CORE_PUBLIC_API_KEY=<only if public Core reads require authentication>
SC_SI_PLATFORM_CORE_WRITE_API_KEY=<only if backend lineage/write integration is used>
```

## Presentation reliability

The production-truth classifier no longer treats any incidental occurrence of the word `unavailable` as a workspace failure. Explicit service failures still degrade correctly, and an unconfigured Platform Core is now identified as configuration debt rather than a missing route.

## Compatibility

- Six primary areas preserved.
- All 35 public routes preserved.
- v4.34.0 SETI and v4.35.1 Exoplanet capabilities preserved.
- Existing source, provenance, evidence-truth, and non-inference boundaries preserved.
