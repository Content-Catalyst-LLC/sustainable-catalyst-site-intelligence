# Site Intelligence v3.24.0 Selector Hydration Audit

## Observed defect

The v3.23.7 backend exposed a global country catalog, but the top application selector could remain as the static HTML fallback containing only Kenya. The defect was visible on the Connected Platform and Overview routes because those routes did not call the route-specific country catalog loader.

## Root cause

The country catalog was initialized only when selected country-oriented workspaces opened. The initial shell could therefore become ready before `loadCountryCatalog()` ran. The Global Data Truth panel was country-aware, but its selected country inherited the unchanged top-level control.

## Repair architecture

### Deterministic global baseline

`loadCountryCatalog()` now requests `/public/data-truth/countries` first. This endpoint supplies the bundled country catalog used by the Global Data Truth contract and allows the selector to hydrate independently of optional live connectors.

### Metadata enrichment

The loader then attempts `/public/countries`. Matching ISO codes enrich the deterministic entries with available platform country metadata. Failure of this enrichment request does not remove countries from the selector.

### Independent region facets

`/public/countries/regions` is loaded separately. A failure now disables only the optional region filter and cannot prevent country selection.

### Startup ownership

`hydrateCountrySelector(initialCountry)` is created during every application startup. Country data loading waits on this task, while the visual shell remains nonblocking under the inherited shell-first hydration contract.

### Selection propagation

After hydration, the application dispatches `scsi:country-catalog-ready`. The Data Truth runtime listens for this event, updates its badge, and refreshes the selected-country view when open.

## Truth-preserving behavior

- The selector does not invent country observations.
- Adding a country to the selector does not imply source coverage.
- The Data Truth panel continues to distinguish eligibility from observed records.
- Unknown remains unknown.
- A zero event count is not treated as evidence that no event exists.
- Kenya remains a default, not a forced or substituted value.

## Browser gate

The release gate requires:

- at least 170 selectable country options;
- Kenya as the initial default when no valid URL country is supplied;
- Brazil present as a selectable option;
- selection of Brazil without a page reload;
- Data Truth heading `Brazil (BRA)`;
- Data Truth badge `BRA`;
- no uncaught browser errors.
