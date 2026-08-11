# Site Intelligence v4.34.0 — SETI, Technosignatures & Radio Signal Intelligence

Site Intelligence v4.34.0 adds a source-bounded SETI environment inside the existing Astronomy / Space workflow without adding a primary area or public navigation route.

## Evidence sources

- Breakthrough Listen Open Data Archive — public observation/data-product search and backend API context.
- Breakthrough Listen 1327-Star Event Tables — published signal-event groups with frequency, drift-rate, SNR and underlying file identifiers.
- SETI Institute Technosearch — published SETI-search coverage and methodology archive.
- NASA Exoplanet Archive TAP — stellar/exoplanet target context used only for orientation and prioritization.

## Truth boundary

**TECHNOSIGNATURE SEARCH EVIDENCE · NOT CONFIRMATION OF EXTRATERRESTRIAL INTELLIGENCE**

Signal events, anomalies, candidate labels, pipeline scores and non-detections remain source-bounded evidence. The platform does not infer extraterrestrial origin, exclude radio-frequency interference, declare a confirmed technosignature, or authorize a public announcement.

## Public contracts

- `GET /public/seti-technosignatures`
- `GET /public/seti-technosignatures/catalog`
- `GET /public/seti-technosignatures/state`
- `POST /public/seti-technosignatures/observation/normalize`
- `POST /public/seti-technosignatures/signal/normalize`
- `POST /public/seti-technosignatures/candidate/normalize`
- `GET /public/seti-technosignatures/export-manifest`
- `GET /public/seti-technosignatures/readiness`

## Browser integration

SETI is entered from the existing Astronomical Observation Environment. Its CSS, JavaScript and panel are lazy-created on entry so the initial Site Intelligence shell stays inside the inherited HTML byte budget. The spectrum visual is explicitly an orientation graphic, not telescope data.

## Architecture

- Six primary areas preserved.
- 35 public navigation routes preserved.
- Existing Space, Ocean, Earth and infrastructure contracts preserved.
- WordPress assets mirror backend assets.
- Service worker caches the new SETI assets.
- Bounded Render release-gate polling retained.
