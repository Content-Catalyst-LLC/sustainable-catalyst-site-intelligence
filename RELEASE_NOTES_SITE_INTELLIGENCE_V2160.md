# Site Intelligence v2.16.0

## Statistical Harmonization and Comparable-Series Engine

Site Intelligence v2.16.0 adds an explicit transformation and comparability layer for statistical series. Raw observations remain inspectable alongside reviewed transformed series, and every transformation records its parameters, input digest, output digest, and sequence.

### Highlights

- Dimension-checked unit conversion
- Per-capita and per-N normalization with supplied denominators
- Explicit monthly, quarterly, and annual period alignment
- Supplied-rate currency conversion and supplied-deflator constant-price adjustment
- Index rebasing with visible base periods
- Geography and definition-version compatibility checks
- Eight missing-data classes without silent imputation
- Raw-versus-transformed views
- Comparable-series diagnostics
- CSV, JSON, and Workbench handoff exports
- Public Harmonize workspace and WordPress shortcodes

### Governance

The engine does not silently normalize values, select exchange rates, impute missing observations, invent geographic equivalence, create composite scores, rank countries, or infer causality.

### Validation

- 442 backend tests passed
- Release contract passed
- Python, JavaScript, PHP, JSON, webmanifest, and YAML checks passed
- Writable harmonization, history, spatial, connector, queue, and cache state excluded from the immutable release
