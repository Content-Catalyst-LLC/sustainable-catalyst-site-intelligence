# Site Intelligence v4.35.0 — Exoplanets, Habitability & Atmospheric Biosignature Intelligence

## Summary
v4.35.0 adds a lazy-loaded Space Intelligence environment for exoplanet system parameters, atmospheric spectroscopy, JWST spectral products, and source-attributed biosignature assessment context. It is attached to Astronomical Observation and does not change the six-primary-area / 35-public-route navigation architecture.

## Evidence sources
1. NASA Exoplanet Archive — Planetary Systems / PSCompPars through TAP.
2. NASA Exoplanet Archive — Atmospheric Spectroscopy table through TAP.
3. Exo.MAST — identifiers, properties and curated exoplanet spectra API.
4. MAST JWST Spectral Data Services — Level-3 spectroscopic pixel and derived products.

Interpretive framework: NASA Astrobiology / NExSS principles that habitability and biosignatures require environmental context, alternative explanations and false-positive assessment.

## Truth boundary
**EXOPLANET & ATMOSPHERIC EVIDENCE · NOT CONFIRMATION OF HABITABILITY OR LIFE**

The release never converts habitable-zone placement into a habitability finding, equilibrium temperature into surface temperature, a spectral feature into automatic molecular confirmation, a molecule into a confirmed biosignature, or a biosignature candidate into a life-detection claim.

## New public contracts
- GET `/public/exoplanet-habitability`
- GET `/public/exoplanet-habitability/catalog`
- GET `/public/exoplanet-habitability/state`
- POST `/public/exoplanet-habitability/planet/normalize`
- POST `/public/exoplanet-habitability/spectrum/normalize`
- POST `/public/exoplanet-habitability/biosignature/normalize`
- GET `/public/exoplanet-habitability/export-manifest`
- GET `/public/exoplanet-habitability/readiness`

## Interface
Astronomical Observation now exposes an **Exoplanets / Atmospheres** action. The new panel lazy-loads its CSS and JavaScript and uses an institutional spectrum-orientation graphic explicitly labeled as not observed spectral data.

## Deployment
The existing bounded Render polling model is retained. Promotion requires exact version/commit/release identity plus a dedicated exoplanet deep gate before the WordPress package is surfaced for installation.
