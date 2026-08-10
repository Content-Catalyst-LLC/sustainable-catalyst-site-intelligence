# Site Intelligence v4.28.0 — Global Energy Infrastructure, Power Systems & Electricity Intelligence

## Scope
Adds an Earth Observation energy-systems environment after Transportation without changing the six primary areas or 35 public routes.

## Source families
- OpenStreetMap power infrastructure / Overpass — global community-mapped plants, generators, substations, lines and cables; ODbL attribution/share-alike obligations apply to database reuse.
- U.S. Energy Information Administration Open Data API v2 — balancing-authority demand, generation, interchange, generator capability and other official U.S. energy series.
- Ember Electricity Data API — CC BY 4.0 cross-country electricity generation, demand, capacity, carbon-intensity and emissions statistics.
- ENTSO-E Transparency Platform — pan-European load, generation, transmission, market and outage publications via the Transparency Platform/API.

## Truth boundary
ENERGY-SYSTEM EVIDENCE · NOT AN OUTAGE, RELIABILITY, SAFETY OR OPERATING-STATUS DETERMINATION

Mapped infrastructure is not automatically energized or operational. Reported capacity is not real-time available capacity. Forecasts are not observations. ENTSO-E unavailability publications are source records rather than Sustainable Catalyst outage declarations. Market prices do not establish retail prices or physical grid reliability. Country statistics do not establish local electricity service.

## Public contracts
- GET /public/energy-systems
- GET /public/energy-systems/catalog
- GET /public/energy-systems/state
- POST /public/energy-systems/feature/normalize
- POST /public/energy-systems/series/normalize
- POST /public/energy-systems/threshold/preview
- GET /public/energy-systems/export-manifest
- GET /public/energy-systems/readiness
