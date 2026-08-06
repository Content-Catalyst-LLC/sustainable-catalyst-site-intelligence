# Site Intelligence v3.23.7 — Global Country Data Truth and Coverage Matrix

## Purpose
Extend Data Truth from a source-level directory into a country-aware disclosure system without treating geographic eligibility as proof that records exist.

## Delivered
- Bundled 177-geography country truth catalog.
- Country-aware source applicability, evidence level, coverage state, operational state, and limitations.
- Public country, source, indicator, and coverage-matrix endpoints.
- Coverage states: available, partial, no recent records, historical only, not applicable, unavailable, and unknown.
- Dated Kenya and Ghana packaged indicator fallbacks remain historical only; other countries remain unknown until verified records exist.
- Interactive selected-country, coverage-matrix, and source-directory views inside the application.
- Country-search matrix filtering and selected-country synchronization.
- Global truth assets are service-worker registered and copied into the WordPress distribution without host-document execution.

## Boundaries
- Eligibility is not observation.
- No recent event records do not prove absence.
- Unknown coverage is never upgraded to available.
- Missing indicators are not silently imputed.
