# Site Intelligence v4.29.0 — Global Digital Connectivity, Broadband & Internet Performance Intelligence

## Purpose
Adds a digital-connectivity evidence layer inside the existing Earth Observation architecture without creating a new top-level public route family.

## Source registry
1. OpenStreetMap telecommunications infrastructure — community-mapped towers, masts, exchanges, antennas and cables.
2. Measurement Lab — CC0 client-initiated network performance measurements and aggregate NDT statistics.
3. World Bank connectivity indicators — harmonized country/economy Internet-use, broadband, mobile and related ICT statistics.
4. FCC Broadband Data Collection / National Broadband Map — U.S. provider-reported fixed/mobile broadband availability and public data APIs/downloads.

## Public contracts
- GET `/public/digital-connectivity`
- GET `/public/digital-connectivity/catalog`
- GET `/public/digital-connectivity/state`
- POST `/public/digital-connectivity/feature/normalize`
- POST `/public/digital-connectivity/measurement/normalize`
- POST `/public/digital-connectivity/availability/normalize`
- POST `/public/digital-connectivity/threshold/preview`
- GET `/public/digital-connectivity/export-manifest`
- GET `/public/digital-connectivity/readiness`

## Truth boundary
**DIGITAL-CONNECTIVITY EVIDENCE · NOT SERVICE AVAILABILITY, OUTAGE, COVERAGE GUARANTEE OR NETWORK-SAFETY DETERMINATION**

Mapped telecom infrastructure is not proof of signal coverage or operation; client-initiated speed tests are not universal local/provider performance; national connectivity statistics are not household-level access; FCC provider-reported availability is not measured speed or a guarantee that service can be installed at a particular moment; zero records do not establish no connectivity.

## Architecture
- Six primary areas preserved.
- 35 public navigation routes preserved.
- Energy Systems defers the v4.29 browser surface.
- Backend and WordPress assets are mirrored byte-for-byte.
- Service-worker registry includes v4.29 assets.
- v4.12 nested runtime-state exclusion remains enforced.
- Bounded, visible Render polling remains in the promotion path.
