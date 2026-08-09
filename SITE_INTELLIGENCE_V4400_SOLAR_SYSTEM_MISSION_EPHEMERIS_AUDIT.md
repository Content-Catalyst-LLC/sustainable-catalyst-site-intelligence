# v4.6.0 Solar System Navigation & Mission Ephemeris Audit

## Architecture

The feature is embedded in the existing `earth` route. It adds an observation destination layer rather than a new application route. This preserves the v4 platform contract of six primary areas and 35 public routes.

## Ephemeris states

The implementation distinguishes three states:

1. **Orientation** — a local, explicitly illustrative solar-system layout. No numerical position claim is made.
2. **Source-attributed ephemeris** — a normalized numerical record supplied with an approved JPL Horizons or NAIF SPICE source URL, epoch, target, frame, position vector, units, and optional velocity vector.
3. **Verified-at-source handoff** — navigation to the registered authoritative or exploratory service. A handoff is not represented as a locally verified response.

## Non-fabrication controls

- No current body position is embedded in the body catalog.
- Approximate AU values exist only for visual ordering and are labeled orientation-only.
- Mission records do not embed a current spacecraft position or trajectory.
- Selecting a mission does not resolve or fabricate its authoritative Horizons/SPICE identifier.
- Local trajectory points remain empty until an authoritative implementation is added in a later release.
- NASA Eyes is not treated as the numerical ephemeris authority for this contract.
- Source normalization rejects non-HTTPS and unregistered source hosts.
- Source-domain recognition is distinct from independent network verification.

## Release gates

The release contract requires the solar-system API, readiness endpoint, browser asset, WordPress asset parity, no-fake-ephemeris/no-fake-trajectory readiness checks, and the inherited v4 route/navigation contracts. The promotion script also requires the live Render deployment to satisfy Solar System Navigation contract/readiness before producing a successful deployment receipt.
