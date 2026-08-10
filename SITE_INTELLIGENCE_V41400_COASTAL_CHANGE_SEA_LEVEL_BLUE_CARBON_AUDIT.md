# Site Intelligence v4.15.0 Audit — Coastal Change, Sea Level & Blue-Carbon Intelligence

## Scope

This audit covers the additive coastal evidence layer introduced after Marine Pollution, Debris & Water-Quality Intelligence.

## Evidence separation

- **Observed water level:** retained as a timestamped station observation with datum context.
- **Tide prediction:** retained as prediction evidence and never marked as observation.
- **Sea-level scenario / inundation:** retained as screening evidence rather than exact flood prediction.
- **Shoreline analysis:** retains analysis period, change rate, units, uncertainty, source extent, and model/analysis class.
- **Coastal habitat:** retains habitat classification and extent without platform-derived carbon quantities or certification claims.

## Blue-carbon safeguards

The platform explicitly sets false for platform-derived carbon stock, sequestration rate, restoration-success verification, and carbon-credit eligibility. A source may contain carbon-context material, but Site Intelligence does not manufacture a carbon quantity from area or habitat class.

## Coastal-hazard safeguards

Scenario preview explicitly refuses parcel-level flood forecasting, exact flood-boundary claims, navigation/permitting use, and automatic safety/evacuation action. Shoreline evidence does not become a property-loss or safety finding.

## Provenance and source constraints

Normalized records require registered source families and HTTPS source hosts. Cross-source indicator combinations remain visible as unsupported in query state and are rejected when normalization requires a registered source/indicator pairing.

## Architecture and packaging

The layer is deferred from the v4.13 marine-pollution panel, mirrored byte-for-byte into the WordPress asset package, added to the service-worker route-asset registry, and protected by the immutable-manifest runtime-state exclusions established after v4.12.0.
