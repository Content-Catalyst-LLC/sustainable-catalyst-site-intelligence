# v4.35.1 Exoplanets, Habitability & Atmospheric Biosignature Audit

## Scope
Public orientation and normalization contracts for exoplanet-system parameters, atmospheric spectra, JWST Level-3 spectroscopy, and source-attributed biosignature assessment records.

## Source boundaries
### NASA Exoplanet Archive — Planetary Systems
Use: planet, host-star, orbital and published equilibrium-temperature context.
Boundary: habitable-zone membership and equilibrium temperature are not direct observations of surface habitability.

### NASA Exoplanet Archive — Atmospheric Spectroscopy
Use: peer-reviewed transmission, eclipse and direct-imaging spectra.
Boundary: spectral data are observational evidence; atmospheric interpretation remains source- and analysis-dependent.

### Exo.MAST
Use: canonical identifiers, planet properties and curated spectra.
Boundary: target context and curated products do not establish biological interpretation.

### MAST JWST Spectral Data Services
Use: calibrated JWST Level-3 spectroscopic products and pixel/derived data.
Boundary: calibrated spectral products do not independently establish molecules, biosignatures, habitability or life.

## Explicit false-inference guards
- `habitable_zone_equals_habitable = false`
- `equilibrium_temperature_equals_surface_temperature = false`
- `spectral_feature_equals_molecule_confirmation = false`
- `molecule_detection_equals_biosignature_confirmation = false`
- `biosignature_candidate_equals_life_detection = false`
- `modeled_abundance_equals_direct_measurement = false`
- `abiotic_false_positive_excluded_by_platform = false`
- `life_confirmed = false`
- `automatic_action_authorized = false`

## UI boundary
The spectrum panel is orientation graphics only and is labeled **ATMOSPHERIC SPECTRUM ORIENTATION · NOT OBSERVED DATA**.

## Navigation
No new primary area and no new public navigation route are introduced. The feature is a lazy-loaded child of Astronomical Observation.
