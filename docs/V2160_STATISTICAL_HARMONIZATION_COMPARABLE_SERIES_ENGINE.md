# Site Intelligence v2.16.0

## Statistical Harmonization and Comparable-Series Engine

This release introduces an explicit transformation and comparability layer for statistical series. Raw source observations are preserved with their units, currencies, price bases, frequencies, geographic definitions, methodology, missing-data classes, and source identity. Every transformation records its parameters, input digest, output digest, time, and sequence.

### Supported transformations

- Dimension-checked unit conversion
- Per-capita and per-N normalization with supplied denominators
- Monthly-to-quarterly, monthly-to-annual, and quarterly-to-annual alignment with explicit `sum`, `mean`, or `latest` rules
- Currency conversion with supplied period-specific rates and rate-source metadata
- Constant-price adjustment with supplied deflators and declared base year
- Index rebasing with a visible base period and target value

### Comparability diagnostics

The engine checks unit dimensions, currency, price basis, frequency, geography code and level, geographic-definition version, and observed-period overlap. Blocking differences prevent paired-value output. Review-level differences remain visible. No silent normalization is permitted. The engine creates no rankings, composite scores, causal claims, or hidden equivalence decisions.

### Missing data

The normalized observation schema distinguishes `observed`, `not_available`, `not_applicable`, `suppressed`, `estimated`, `provisional`, `break_in_series`, and `unknown`. Missing denominators, exchange rates, or deflators produce explicit unavailable values rather than imputation.

### Storage and deployment

The default implementation is file-backed and requires no paid database. For persistent production series and lineage receipts, configure the harmonization paths on durable storage. The writable `backend/data/statistical_harmonization_v2160/` directory is excluded from Git and immutable release manifests.

### Workbench handoff

Reviewed series can be exported as read-only Workbench handoff packets with units, frequency, geography, observations, and lineage intact.

### Public surfaces

- `/app/?view=harmonization`
- `/public/harmonization`
- `/public/harmonization/standards`
- `/public/harmonization/methodology`
- `/public/harmonization/series`
- `/public/harmonization/compare`
- `/public/harmonization/export`
- `[sc_public_comparable_series]`

### Private surfaces

- `/admin/harmonization/control-center`
- `/admin/harmonization/series/register`
- `/admin/harmonization/transform`
- `/admin/harmonization/compare`
- `/admin/harmonization/workbench-handoff`
- `[sc_statistical_harmonization_control_center]`
