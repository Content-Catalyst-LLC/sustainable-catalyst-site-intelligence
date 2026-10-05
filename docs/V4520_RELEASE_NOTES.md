# Site Intelligence v4.52.0 — Predictive Spatial Intelligence Consumer

v4.52.0 adds a provider-neutral consumer layer for spatially contextualized predictive artifacts. Site Intelligence can normalize and validate forecast/probability objects, bind them to canonical spatial layers and evidence, query them across space/time, compare alternatives without ranking models, preserve scenario alternatives, consume calibration/uncertainty evidence, and attach prediction context to v4.51 spatial research objects without mutating them.

## Boundaries

- Predictions remain model-conditional derived information, never observations or truth.
- Probability is not converted into certainty.
- Spatial intersection does not establish impact or causality.
- Site Intelligence does not train, retrain, automatically select, or automatically rank models.
- Workspace/Core remain external execution/object authorities; this release consumes supplied artifacts and performs no provider network fetch.
- Existing `/public/models`, `/public/forecasts`, and `/public/forecast-evaluations` remain available.

## Runtime

- Capability registry generation: 1.9.0
- Routes: 1,431
- Modularized routes: 122
- Capability families: 23
- Predictive-spatial routes: 12/12 modular
- Release-bound files: 34
