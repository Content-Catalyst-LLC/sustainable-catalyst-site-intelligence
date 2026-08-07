# Site Intelligence v3.25.0
## Country Selector Hydration and Global Selection Repair

### Release purpose

Site Intelligence v3.23.7 shipped the Global Country Data Truth catalog and coverage matrix, but the top application country selector could remain at its static one-option markup on routes that did not explicitly initialize a country workspace. This patch makes global country selection part of the application bootstrap contract rather than a route-dependent side effect.

### Repairs

- Hydrates the main country selector during every application startup route.
- Uses the bundled Global Data Truth country catalog as the deterministic baseline.
- Enriches catalog entries with the primary `/public/countries` response when it is available.
- Keeps country selection usable when the optional region-facet endpoint is unavailable.
- Preserves a supported `?country=ISO3` URL selection.
- Falls back to Kenya only when no valid requested or retained country is present.
- Dispatches a `scsi:country-catalog-ready` event after catalog hydration.
- Refreshes an open Data Truth panel after programmatic selector hydration.
- Retains the v3.23.6.4 route, service-worker, loading, and WordPress embed stability contracts.

### Browser acceptance contract

The mandatory selector gate loads the complete shipped shell, waits for at least 170 selector options, confirms Kenya remains the initial default, verifies Brazil is present, changes the selector to Brazil, opens Data Truth, and requires the panel badge and heading to change to `BRA` and `Brazil (BRA)` without a reload.

### Deployment boundary

This package does not deploy itself from the build environment. The macOS installer validates the source twice, promotes the exact Git tree to GitHub and Render, verifies the live catalog and selector runtime, and only then permits installation of the WordPress ZIP.
