# Sustainable Catalyst Site Intelligence v2.17.0

## Model Registry, Forecast Evaluation, and Early-Warning Indicators

Site Intelligence v2.17.0 adds a governed model and forecast evidence layer to the public observatory. The release registers versioned model cards, preserves attributable forecast records, evaluates forecasts against overlapping observations, exposes uncertainty and calibration evidence, detects performance drift for review, and creates threshold-based early-warning signals without granting autonomous decision authority.

### Major additions

- Versioned public/private model registry and model cards
- Intended-use, limitations, provenance, lifecycle, expiry, and prohibited-use metadata
- Published forecast ingestion with optional prediction intervals and confidence levels
- MAE, RMSE, bias, MAPE, and sMAPE evaluation
- Empirical interval coverage, calibration gap, and interval-width diagnostics
- Recent-versus-baseline drift review
- Above, below, percent-increase, and percent-decrease warning rules
- Public-safe methodology, diagnostics, models, forecasts, evaluations, warning events, and exports
- Token-protected model, forecast, evaluation, warning, and governance operations
- Dedicated public application Models workspace
- Public and administrator-only WordPress shortcodes
- File-backed zero-cost operation with configurable persistent paths

### Governance boundaries

The release does not support individual targeting, surveillance, emergency dispatch, military targeting, autonomous consequential decisions, hidden model substitution, silent retraining, guaranteed outcomes, or unsupported causal claims. Forecasts are not relabeled scenarios, and threshold crossings remain human-review signals.

### Deployment note

Writable model cards, forecasts, evaluations, warning rules, and warning events are excluded from the release archive. Configure a persistent Render disk or another durable path before relying on historical production model records.
