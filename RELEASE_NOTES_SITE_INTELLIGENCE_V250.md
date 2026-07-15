# Sustainable Catalyst Site Intelligence v2.5.0

## Humanitarian, Conflict, and Displacement Observatory

Site Intelligence v2.5.0 adds a source-aware public workspace for humanitarian reporting, conflict-related records, forced-displacement context, civilian protection, humanitarian access, and hazard exposure.

## Public workspace

- Route: `/app/?view=humanitarian`
- WordPress shortcode: `[sc_humanitarian_conflict_displacement_observatory height="1450"]`

## Public APIs

- `GET /public/humanitarian-conflict-displacement`
- `GET /public/humanitarian-conflict-displacement/records`
- `GET /public/humanitarian-conflict-displacement/facets`
- `GET /public/humanitarian-conflict-displacement/timeline`
- `GET /public/humanitarian-conflict-displacement/displacement`
- `GET /public/humanitarian-conflict-displacement/country-profile`
- `GET /public/humanitarian-conflict-displacement/access`
- `GET /public/humanitarian-conflict-displacement/brief`
- `GET /public/humanitarian-conflict-displacement/diagnostics`

## Data integration

The workspace combines:

- Existing Site Intelligence public event feeds
- Sustainable Catalyst Core public live observations
- Core international-law and human-rights records
- Core official statistics and displacement-related indicators

Core credentials remain server-side. Provider keys, raw ingestion identifiers, authorization values, and sensitive URL query parameters are removed from public records.

## Responsible-use boundaries

The release does not:

- Fabricate crisis records when sources are unavailable
- Infer legal responsibility or combatant status
- Determine refugee or protection status
- Score individual risk
- Make eligibility or benefit decisions
- Support military targeting
- Act as an emergency warning or dispatch service

Displacement stocks, movement flows, registrations, estimates, events, reports, and legal records remain distinct.

## Interface

The public workspace includes:

- Country, category, source, time-window, and keyword filters
- Global evidence map
- Chronological timeline
- Source-aware record cards
- Displacement-specific view and country profiles
- Humanitarian-access context
- CSV export
- Shareable filtered URLs
- Saved View support
- Decision Studio handoff

## Validation

- 350 backend tests passed
- Python compilation passed
- JavaScript syntax passed
- PHP syntax passed
- JSON and YAML parsing passed
- Release contract passed
- Public evidence and audit cross-references passed
- No paid API dependency introduced
