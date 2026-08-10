# Site Intelligence v4.12.0 — Underwater Observation & Visual Evidence Audit

## Scope

This release adds a visual-evidence layer after the v4.7.0 seafloor workflow. It is deliberately an evidence-discovery and normalization system, not a synthetic underwater-rendering system.

## Registered source boundaries

### Ocean Networks Canada Oceans 3.0 / SeaTube

Registered for observatory/camera media discovery and related deployment context. Coverage is deployment- and time-specific. Station presence does not imply a visual record exists for every requested point, depth, or time. Rights and attribution are retained per source asset rather than inferred globally.

### FathomNet

Registered for underwater images and source-attributed annotations. Human and machine labels remain annotation evidence. Machine inference is never converted into a verified taxonomic observation by Site Intelligence. Contributor/asset rights remain explicit.

### NOAA Ocean Exploration / NCEI

Registered for expedition/dive media references, ROV video/image context, dive/navigation records, and related archive discovery. A dive track or expedition footprint does not establish media coverage at every location. Public-domain statements are preserved only when attached to the applicable NOAA Video Portal media context.

## Non-fabrication controls

The default state contains no media URL, no thumbnail URL, no source record ID, no verified location/depth/time match, no loaded annotation, and no synchronized sensor context. Missing media remains missing.

The browser stage is labeled `ORIENTATION VIEW · NO UNDERWATER MEDIA LOADED` and renders no source image pixels.

## Annotation controls

Bounding boxes must be `[x, y, width, height]` with nonnegative width/height. Confidence, when supplied, is bounded to 0–1. `model-inference` records can retain source-provided taxonomy metadata but cannot become `verified_taxonomic_observation=true` through this contract.

## URL controls

`source_url`, `media_url`, and `thumbnail_url` must use HTTPS and must resolve to a registered source host for the selected provider. Arbitrary third-party media URLs are rejected.

## Rights controls

Rights are not inferred from repository/catalog presence. `rights_verified` requires an explicit rights statement in a normalized source record. The source-level catalog describes known rights boundaries but does not grant a reuse license.

## Route and performance controls

No new top-level route is added. Underwater Observation is loaded through the existing deferred Seafloor shell and does not add a first-load application script. The complete base shell remains at 53 first-party scripts, six primary areas, and 35 routes.
