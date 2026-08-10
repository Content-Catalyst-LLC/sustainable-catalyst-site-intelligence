# Site Intelligence v4.13.0 — Marine Pollution, Debris & Water-Quality Audit

## Scope

Adds a deferred marine pollution evidence environment inside Earth Observation after Human Activity & Protection.

## Registered source families

1. NOAA NCEI Marine Microplastics
2. EMODnet Chemistry
3. Copernicus Marine Biogeochemistry
4. Water Quality Portal

## Evidence separation

The release keeps observed microplastics, observed litter, discrete chemistry/water-quality measurements, model analyses, forecasts, non-detects, and quality flags as distinct evidence classes.

## Required non-inference behavior

- Zero returned records are never represented as clean water.
- Non-detects are never automatically converted to numeric zero.
- Modeled or forecast fields are never represented as in-situ samples.
- Debris observations do not trigger source/actor attribution.
- Threshold conditions do not trigger regulatory, health, exposure, ecological-harm, or enforcement conclusions.
- No automatic action is authorized by threshold preview.

## Architecture

The release adds no primary navigation area and no v4 workspace route. It extends the established ocean sequence and preserves the six-area / 35-route platform contract.

## Browser behavior

The interface is dynamically loaded from the v4.12 Human Activity environment, runs in the direct application and WordPress iframe, keeps host-page isolation, and exposes an evidence manifest without fabricating source records.

## Result

PASS — v4.13.0 satisfies the Marine Pollution, Debris & Water-Quality evidence boundary and inherited platform architecture.
