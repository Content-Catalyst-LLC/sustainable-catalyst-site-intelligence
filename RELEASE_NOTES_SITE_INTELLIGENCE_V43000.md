# Site Intelligence v4.30.0 — Global Industrial Facilities, Manufacturing & Trade-Flow Intelligence

## Purpose
Adds an industrial/manufacturing/trade evidence layer inside the existing Earth Observation architecture without creating a new top-level public route family.

## Source registry
1. OpenStreetMap industrial facilities — community-mapped factories, works, refineries, warehouses/logistics sites and industrial land use.
2. World Bank manufacturing indicators — harmonized manufacturing value-added, GDP share, growth and technology-intensity series.
3. World Bank Global Economic Monitor — higher-frequency industrial-production and merchandise-trade macroeconomic series.
4. World Bank WITS Trade Stats — public CC BY 4.0 bilateral merchandise-trade aggregations and derived trade indicators based on UN COMTRADE / UNCTAD source data.

## Public contracts
- GET `/public/industrial-manufacturing`
- GET `/public/industrial-manufacturing/catalog`
- GET `/public/industrial-manufacturing/state`
- POST `/public/industrial-manufacturing/feature/normalize`
- POST `/public/industrial-manufacturing/series/normalize`
- POST `/public/industrial-manufacturing/trade-flow/normalize`
- POST `/public/industrial-manufacturing/threshold/preview`
- GET `/public/industrial-manufacturing/export-manifest`
- GET `/public/industrial-manufacturing/readiness`

## Truth boundary
**INDUSTRIAL & TRADE EVIDENCE · NOT OPERATING STATUS, FACILITY OUTPUT OR SUPPLY-CHAIN DEPENDENCY DETERMINATION**

Mapped industrial geometry is not proof that a plant is operating; national manufacturing statistics do not establish facility output or utilization; industrial-production series are not plant telemetry; trade statistics are not physical shipment tracking; bilateral trade does not by itself establish supplier dependency, shipment routing, origin content or current inventory; zero records do not establish absence of industrial or trade activity.

## Architecture
- Six primary areas preserved.
- 35 public navigation routes preserved.
- Digital Connectivity defers the v4.30 browser surface.
- Backend and WordPress assets are mirrored byte-for-byte.
- Service-worker registry includes v4.30 assets.
- v4.12 nested runtime-state exclusion remains enforced.
- Bounded, visible Render polling remains in the promotion path and now includes an Industrial deep gate.
