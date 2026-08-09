# Site Intelligence v4.6.0 — Water Column & Depth Explorer Audit

## Scope

Audit the Water Column implementation for scientific non-fabrication, source boundaries, depth semantics, profile normalization, browser integration, v4 route preservation, and deployment compatibility.

## Source registry

### Argo / Argovis
- Public Argo data documentation identifies profile, trajectory, metadata, technical, real-time, and delayed-mode QC data.
- Argo documentation identifies Argovis as an API path for time/space selections, individual profiles, floats/platforms, and metadata.
- Registered API/documentation hosts are restricted to Argo/Argovis domains.

### Copernicus Marine
- Registered as a 3-D gridded ocean product path rather than an in-situ observation substitute.
- Access is dataset-specific and can include analysis, forecast, reanalysis, and model products.
- Public state contains no Copernicus credentials.

### Ocean Networks Canada Oceans 3.0
- Registered as observatory/mobile/cast/instrument discovery and data-product access.
- ONC regional observing coverage is not represented as global coverage.
- Fixed-depth instruments are not represented as vertical profiles without a source profile/cast record.

## Non-fabrication controls

PASS — State contains `value: null` before a source record is loaded.

PASS — `depth_sample_verified` is false until an exact source sample is present.

PASS — v4.6.0 interpolation is disabled.

PASS — nearest-sample substitution is disabled.

PASS — pressure/depth conversion is disabled unless a future explicit method provides and documents it.

PASS — missing samples remain missing.

PASS — source-host allowlists reject arbitrary HTTPS domains.

## Profile normalization

Normalized profiles retain:
- profile identity
- platform identity when present
- source URL and dataset identity
- evidence type
- location and observation/retrieval time
- exact source depth
- optional source pressure
- value and source unit
- source quality flags
- source sample identity when present

Samples are ordered by depth for presentation only. Duplicate normalized depth entries are rejected to avoid ambiguous exact-depth resolution.

## Exact-depth resolution

An exact source depth can return its source value. If the requested depth falls between samples, the resolver returns no requested-depth value. The nearest available sample may be reported only as context, with `value_withheld_as_target_value: true`.

## UI and performance

The Water Column JS/CSS is loaded from the existing Ocean Surface shell rather than adding another script tag to the base HTML. Base HTML therefore remains at its inherited performance budget rather than expanding with the new panel.

The stage is explicitly labeled `ORIENTATION FIELD · NO PROFILE SAMPLE RENDERED`.

## Architecture

PASS — six primary v4 areas preserved.

PASS — 35 public routes preserved.

PASS — Water Column remains inside the Earth Observation/Ocean workflow.

## Deployment gate

The v4.6 live promotion gate independently checks Water Column overview, catalog, state, readiness, and shipped browser JS. A deployment cannot report success if the runtime claims a fabricated depth value, enables interpolation/nearest substitution, omits required sources, or fails to ship the v4.6 Water Column client.
