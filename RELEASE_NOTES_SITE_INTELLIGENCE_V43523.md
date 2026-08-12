# Site Intelligence v4.35.23 — Canonical Country Identity & Selector Routing Repair

v4.35.23 repairs the country-selection defect in which Israel could leave the Palestine profile on screen and Palestine selection could fail to commit visibly. The release removes live statistical-provider catalogs from the country identity boundary.

## What changed

- Added a first-party canonical 172-country ISO3/ISO2 identity registry shared by selector, backend country resolver, Data Truth country catalog, and cartographic focus.
- Locked `ISR → IL → Israel` and `PSE → PS → Palestine` as independent canonical identities.
- World Bank country metadata is now enrichment only; an unavailable or partial World Bank country catalog cannot remove a selectable country or redefine its canonical identity.
- Country selection commits `?view=country&country=<ISO3>` before optional indicator retrieval, so the selected country state does not appear ignored while upstream data loads.
- Country overview/trend responses are checked against the requested ISO3 code before rendering. Cross-identity responses are rejected instead of displaying the wrong country.
- Cartographic country focus now merges the bundled canonical country catalog before optional live metadata.
- Added deterministic rapid-switch browser regression coverage for Palestine→Israel and Israel→Palestine.
- Added `/public/country-identity/readiness` to the first-party release gate; identity readiness performs no external network calls and upstream health remains non-blocking.

## Inherited safeguards

v4.35.22 evidence reconciliation/scope integrity, v4.35.21 Palestine data federation/Wikimedia context, v4.35.20 country-linked record recovery, and v4.35.19 production soak/semantic truth remain intact.

## Validation

- 1,644/1,644 deterministic tests passed.
- Dedicated Israel/Palestine selector-routing browser regression passed.
- 35/35 desktop, 35/35 mobile, and 35/35 iframe workspace routes were ready with zero degraded routes.
- 135 JSON/GeoJSON files and 152 JavaScript files validated; PHP syntax passed; static security scan returned zero findings.
- Experience budgets remained below the inherited limits.
- Final immutable repository manifest contains 2,432 release files.
