# Site Intelligence v4.35.25 — Country Intelligence Presentation & Evidence Hierarchy

v4.35.25 makes the Country workspace reflect the multi-source evidence architecture already present in Site Intelligence. The release changes presentation and interpretation boundaries rather than adding another broad connector family.

## What changed

- Adds a Country Intelligence Brief above the indicator grid so source roles, evidence status, reference-period limits, and operational boundaries are visible before individual numbers.
- Separates **Conditions Now** from annual/structural statistics. Current operational and humanitarian records no longer share the same visual meaning as national access baselines.
- Labels source roles explicitly: operational, primary official, sector official, intergovernmental, harmonized benchmark, and published evidence.
- Presents World Bank annual country series as **HARMONIZED BENCHMARK** evidence rather than allowing a fresh HTTP retrieval to imply current operational truth.
- Adds a hard interpretation boundary for structural electricity access: the statistic does not establish current electricity supply, outage duration, grid functionality, hours of service, reliability, or generator dependence.
- Adds an equivalent boundary for structural drinking-water access: annual access does not establish current continuity, pressure, availability, or quality.
- Promotes source publisher names in the evidence-reconciliation panel so users can see who published the selected candidate instead of only an internal source identifier.
- Renames generic metric detail actions to **Evidence details** and makes evidence class/scope part of the card hierarchy.
- Changes the country source/interpretation footer from World-Bank-centric language to role-aware multi-source language.
- Adds `/public/country-evidence-presentation/readiness` and makes its network-free semantic checks part of deployment verification.
- Adds the presentation stylesheet to the critical offline shell so the evidence hierarchy remains legible after recovery/offline startup.

## Palestine-specific effect

A structural value such as `Access to electricity — 100%` remains visible when it is a valid published baseline, but it is visually and semantically subordinate to current operational evidence. The card is labeled as a harmonized/structural benchmark and carries an explicit warning that it does not measure present service availability.

PCBS remains the preferred statistical authority for exact supported Palestine concepts when a compatible candidate is present. World Bank remains useful for cross-country comparison/fallback evidence. Operational humanitarian evidence is kept in a separate Conditions Now layer.

## Scope boundary

This release does **not** yet add the facility-level hospital/school ingestion planned for the following operational-evidence builds, and it does not perform the dedicated mobile/Ocean/Space navigation redesign. Its job is to make the country evidence already available materially clearer and more authoritative.

The repository contains no literal public-app `4.0 Direction` label. v4.35.25 does not introduce that legacy wording; if it remains on a WordPress editorial page after deployment, that page content is outside this application bundle and should be updated separately.

## Validation

- 1,657/1,657 deterministic tests passed.
- Country evidence presentation browser regression passed.
- Hostile Palestine/Israel navigation browser regression passed.
- 35/35 desktop, 35/35 mobile, and 35/35 iframe routes ready with zero degraded routes.
- 135 JSON/GeoJSON files parsed; 152 JavaScript files validated; PHP syntax passed; static security scan returned zero findings.
- Core `app.css`: 101,860/102,000 bytes. The dedicated country-presentation stylesheet is 2,773 bytes.
- HTML + core CSS + country-presentation CSS + application JS: 483,688/500,000 bytes.
