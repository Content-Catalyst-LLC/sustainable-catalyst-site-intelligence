# Site Intelligence v3.26.0 Assurance Audit

## Assurance boundary

The v3.26.0 assurance layer is deliberately methodological. It does not certify models, sources, institutions, predictions, or decisions. It exposes the conditions required for a user to understand whether a direct comparison is methodologically aligned, which assumptions changed a scenario result, and whether a model card contains the minimum public disclosure fields.

## Comparison dimensions

The release checks six dimensions before allowing a direct-difference interpretation: unit, definition identifier, period, frequency, price basis, and seasonal adjustment. Missing values remain missing. Incompatible records are marked `review_required` rather than automatically transformed.

## Scenario sensitivity

Low/base/high assumptions are evaluated deterministically. The base scenario applies all base assumptions. Sensitivity rows vary one assumption at a time while holding the other assumptions at their base values. The reported minimum/maximum envelope is the range of those supplied cases and is explicitly non-probabilistic.

## Model-card review

Required fields: model ID, title, model version, intended use, limitations, prohibited uses, inputs, outputs, uncertainty, validation, and provenance. Completeness is a documentation status only. The release does not claim that a complete model card proves correctness, calibration, fairness, or suitability.

## Public method cards

Two non-predictive method cards ship with the release: Transparent Arithmetic Scenario and Comparison Compatibility Review. Registered public models may be surfaced from the existing model-governance registry when available; absence of registered models is not treated as a failure.

## Reproducibility and integrity

Every comparison review, scenario review, model-card review, and package includes deterministic fingerprints over normalized disclosed content. These fingerprints are change detectors, not cryptographic attestations of upstream source authority.

## Preserved safeguards

v3.26.0 retains the inherited global country selector, Data Truth coverage states, record-level provenance, Data Truth Control Plane, unified analytical state, fixed WordPress viewport, single-owner bootstrap, mutation-observer safeguards, production soak, and no-automatic-service-worker-reload contract.
