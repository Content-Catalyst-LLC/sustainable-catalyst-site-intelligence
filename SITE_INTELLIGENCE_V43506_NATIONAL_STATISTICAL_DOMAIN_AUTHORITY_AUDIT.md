# Site Intelligence v4.35.9 — National Statistical & Domain-Authority Connector Audit

## Purpose

Expansion v4.35.9 increases direct access to first-party national statistical authorities instead of routing country evidence primarily through international aggregators.

## New connectors

| Connector | Authority | Mode | Authentication | Primary use |
|---|---|---|---|---|
| PCBS PxWeb | Palestinian Central Bureau of Statistics | LIVE | Public | Palestine official statistics / SDGs |
| Statistics Canada WDS | Statistics Canada | LIVE | Public | Canada official statistical vectors |
| ONS API | UK Office for National Statistics | LIVE | Public | UK official datasets and observations |
| ABS Data API | Australian Bureau of Statistics | LIVE | Public | Australia SDMX official statistics |
| BLS Public Data API v1 | U.S. Bureau of Labor Statistics | LIVE | Public | U.S. labor/prices/economic time series |

## Source-interface notes

- PCBS publicly exposes interactive PxWeb databases for SDG indicators. The Site Intelligence base API route is configurable because PCBS does not expose a separate API documentation page in the repository audit.
- Statistics Canada WDS is intended for programmatic access to discrete data and metadata updates.
- ONS API is open and unrestricted and uses explicit dataset editions and versions.
- ABS Data API is SDMX 2.1 compatible and no longer requires API keys.
- BLS API v1 is public without registration; Site Intelligence intentionally uses the bounded public interface rather than requiring v2 registration.

## Semantic safeguards

The Palestine electricity issue is a release-level regression target: an access-to-electricity percentage is a structural statistical indicator tied to its observation period, not evidence of present electricity availability, grid reliability, or continuity. PCBS records preserve the source period and metadata and cannot be promoted to an operational claim without a separate operational source.

## Audit result

184 registrations / 101 machine-readable / 66 implemented-discovery-config-gated / 46 LIVE / 8 DISCOVERY / 12 AUTH_REQUIRED / 45 registered-but-not-retrieved / 0 stale implemented connectors.
