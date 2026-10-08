# Site Intelligence v4.55.3.2.2 — Browser API Transport & CORS Repair

This corrective release fixes the browser/API transport path discovered after v4.55.3.2.1. The standalone browser runtime could classify the site as Offline while the FastAPI service was healthy because its cross-origin health request carried `X-SCSI-Runtime-Diagnostic`, but the production CORS allow-header policy did not permit that header.

## Changes

- FastAPI CORS now explicitly permits `X-SCSI-Runtime-Diagnostic`.
- Ordinary public runtime GET probes no longer require the custom diagnostic header, avoiding an unnecessary preflight dependency.
- The production backend deployment helper performs a real OPTIONS `/health` preflight from `https://intelligence.sustainablecatalyst.com` and fails deployment if the origin/header contract is not accepted.
- Strict health semantics from v4.55.3.2.1 remain: browser/network loss or canonical `/health` failure can be Offline; optional/domain failures are Degraded.
- Economics country-context repair remains in force. No new domain records are created or fabricated. Substantive Economics/data activation remains v4.55.4.

No API routes were added. Route inventory remains 1518 total / 209 modularized / 31 capabilities / 0 unclassified. Capability registry advances to 2.6.2.
