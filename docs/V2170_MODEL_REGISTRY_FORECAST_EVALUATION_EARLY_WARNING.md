# Site Intelligence v2.17.0

## Model Registry, Forecast Evaluation, and Early-Warning Indicators

This release introduces an auditable governance layer for analytical models, published forecasts, forecast evaluations, model drift review, and threshold-based early-warning indicators. Every registered model has a named version and a model card recording its provider, intended use, limitations, target, geography, forecast horizon, training and evaluation periods, uncertainty method, lifecycle status, visibility, expiry, prohibited uses, and content digest.

### Model registry

- Versioned statistical, mechanistic, machine-learning, ensemble, and externally published model cards
- Draft, active, paused, retired, and expired lifecycle states
- Public and private visibility boundaries
- Required intended-use and limitations statements
- Explicit human-review requirements
- No individual-level data or automatic consequential decision authority

### Forecast records

Forecasts are accepted only for active registered models. Each record preserves the issuing model and version, issue time, target, geography, frequency, forecast values, optional prediction intervals, confidence level, uncertainty method, source reference, visibility, and SHA-256 digest. Forecasts are explicitly labeled as forecasts and are not silently substituted for user-authored scenarios.

### Evaluation and calibration

Evaluation requires overlapping forecast and observed periods. The engine reports mean absolute error, root mean squared error, signed bias, mean absolute percentage error when defined, symmetric mean absolute percentage error, interval empirical coverage, calibration gap, and mean interval width. Recent-period MAE is compared with a declared baseline to produce stable, watch, or review drift signals. These are review diagnostics, not proof of concept drift or future accuracy.

### Early-warning indicators

Rules support above-threshold, below-threshold, percent-increase, and percent-decrease conditions. Each event preserves the evaluated evidence, threshold, direction, severity, match status, and digest. A threshold crossing is a review signal only: it does not establish causation, dispatch an emergency response, or guarantee an outcome.

### Governance boundaries

The release prohibits individual targeting or surveillance, emergency dispatch, military targeting, autonomous legal, medical, financial, humanitarian, employment, credit, or policing decisions, hidden model substitution, silent retraining, unlabeled forecast revision, guaranteed-outcome claims, and unsupported causal claims.

### Storage and deployment

The default implementation is file-backed and requires no paid database. For persistent production model cards, forecasts, evaluations, warning rules, and warning events, configure the model-governance paths on durable storage. The writable `backend/data/model_governance_v2170/` directory is excluded from Git and immutable release manifests.

### Public surfaces

- `/app/?view=models`
- `/public/model-governance`
- `/public/model-governance/methodology`
- `/public/model-governance/diagnostics`
- `/public/models`
- `/public/models/{model_id}`
- `/public/forecasts`
- `/public/forecast-evaluations`
- `/public/early-warning`
- `/public/model-governance/export`
- `[sc_public_model_forecasts]`

### Private surfaces

- `/admin/model-governance/control-center`
- `/admin/model-governance/models/register`
- `/admin/model-governance/forecasts/ingest`
- `/admin/model-governance/evaluations/run`
- `/admin/model-governance/warnings/register`
- `/admin/model-governance/warnings/evaluate`
- `/admin/model-governance/export`
- `[sc_model_forecast_control_center]`
