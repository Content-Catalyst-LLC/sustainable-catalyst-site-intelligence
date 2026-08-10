# v4.29.0 Digital Connectivity Audit

## Evidence separation

| Evidence | What it can support | What Site Intelligence must not infer |
|---|---|---|
| OSM telecom feature | mapped infrastructure geometry/attributes | coverage, signal, operation, ownership, legal access, live service |
| M-Lab measurement | sampled TCP/network performance at measurement time | universal local performance, advertised tier, provider compliance, outage |
| World Bank ICT statistic | harmonized national/economy indicator | household-level access, local coverage, affordability, individual usage |
| FCC BDC availability | provider-reported U.S. availability/coverage | measured performance, adoption, affordability, guaranteed installation, current operation |

## Safety / interpretation boundaries
- No outage declaration.
- No network-safety determination.
- No provider-compliance finding.
- No coverage guarantee.
- No inference that an unmapped tower or empty query means infrastructure is absent.
- No inference that a speed-test sample represents all customers or times.
- No automatic action authorization.

## Licensing / source-selection note
v4.29 deliberately avoids source registries whose current terms create avoidable non-commercial restrictions for this product line. M-Lab measurement data are CC0; the selected World Bank indicator distribution is CC BY 4.0; FCC public broadband availability data are publicly released government data; OpenStreetMap data retain ODbL attribution/share-alike obligations.

## Release architecture
The v4.29 surface is additive inside Earth Observation. It does not change the six primary areas or 35 public navigation routes. The backend contract and WordPress browser assets remain independently verifiable.
