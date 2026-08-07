# Site Intelligence v3.26.0 — Comparative, Scenario, and Model Assurance

## Purpose

Site Intelligence v3.26.0 adds an explicit assurance layer around comparison, transparent scenarios, and model governance. The release does not add autonomous judgment or hidden normalization. It makes compatibility, assumptions, sensitivity, uncertainty, model-card completeness, and reproducibility visible before analytical outputs are interpreted or shared.

## New public contracts

- `GET /public/assurance`
- `POST /public/assurance/comparison`
- `POST /public/assurance/scenario`
- `POST /public/assurance/model-review`
- `GET /public/assurance/model-cards`
- `POST /public/assurance/package`

## Comparison assurance

Comparison review checks unit, definition identifier, period, frequency, price basis, and seasonal-adjustment compatibility. Missing numeric values are disclosed. Direct differences are withheld when the supplied records are not explicitly compatible. The assurance layer performs no silent normalization and no missing-value imputation.

## Scenario assurance

Scenario review maintains an explicit assumption ledger with percent or absolute transformations. Optional low/base/high values produce one-assumption-at-a-time sensitivity results and a deterministic output envelope. The envelope is not presented as a probability, confidence interval, forecast, causal result, or recommendation.

## Model assurance

Model-card review requires model identity and version, intended use, limitations, prohibited uses, inputs, outputs, uncertainty, validation, and provenance. Completeness is intentionally distinct from predictive validity, accuracy, safety, fairness, or institutional approval. Autonomous consequential decision authority and individual risk scoring are outside the public assurance boundary.

## Reproducibility

Assurance packages combine comparison review, scenario review, optional model-card review, notes, and explicit boundaries under a SHA-256 content-change fingerprint. The fingerprint detects package changes; it does not authenticate source truth.

## Interface

The Scenarios workspace includes a Comparative · Scenario · Model Assurance panel. It summarizes comparison dimensions, scenario modes, method cards, and responsible-use boundaries while preserving all inherited country selector, Data Truth, Record Provenance, cross-view state, service-worker, and WordPress embed behavior.
