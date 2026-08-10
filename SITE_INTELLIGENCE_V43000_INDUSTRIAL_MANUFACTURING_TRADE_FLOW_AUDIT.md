# v4.30.0 Industrial / Manufacturing / Trade-Flow Audit

## Evidence separation

| Evidence | What it can support | What Site Intelligence must not infer |
|---|---|---|
| OSM industrial feature | community-mapped industrial geometry and descriptive attributes | current operation, output, employment, ownership, regulatory status, legal access |
| World Bank manufacturing statistic | harmonized country/economy manufacturing structure and trends | plant-level output, utilization, employment, profitability, real-time production |
| World Bank GEM industrial/trade series | national macroeconomic industrial-production and merchandise-trade trend context | plant telemetry, specific disruption, shortage, causal event, physical shipment |
| WITS Trade Stats | reported/aggregated bilateral merchandise-trade values and derived indicators | shipment tracking, route, supplier dependency, origin content, inventory, customs/sanctions compliance |

## Safety / interpretation boundaries
- No plant operating-status determination.
- No facility-output or utilization estimate from national aggregates.
- No disruption, shortage or shutdown declaration from a threshold comparison.
- No bilateral-trade-to-supply-chain-dependency inference.
- No physical shipment or routing inference from customs/trade statistics.
- No inference that empty results mean no industry or trade.
- No automatic action authorization.

## Licensing / source-selection note
The release uses OpenStreetMap under ODbL obligations and World Bank datasets distributed as public open data. World Bank WITS Trade Stats is published in the World Bank Data Catalog under CC BY 4.0. The design avoids paid facility registries as a required production dependency.

## Release architecture
The v4.30 surface is additive inside Earth Observation. It does not change the six primary areas or 35 public navigation routes. The backend contract and WordPress browser assets remain independently verifiable.
