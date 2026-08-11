# Site Intelligence v4.35.11 — National Statistical & Domain-Authority Connector Expansion

Site Intelligence v4.35.11 expands the authoritative-data layer with five direct national statistical authorities while preserving the v4.35.3.1 deployment/source-health separation and all existing connector routes.

## Added authoritative interfaces

1. **Palestinian Central Bureau of Statistics (PCBS) PxWeb** — bounded table metadata and JSON-stat data retrieval. Structural electricity-access statistics remain explicitly distinct from present supply continuity, reliability, outages, or operating conditions.
2. **Statistics Canada Web Data Service (WDS)** — bounded vector retrieval for discrete official-statistics updates, retaining vector identity and source response metadata.
3. **UK Office for National Statistics (ONS) API** — versioned observation retrieval with explicit edition/version and bounded dimension filters.
4. **Australian Bureau of Statistics (ABS) Data API** — bounded SDMX 2.1 data retrieval using explicit dataflow, key, time bounds and observation limits.
5. **U.S. Bureau of Labor Statistics (BLS) Public Data API v1** — bounded public time-series retrieval with year/period/footnote preservation.

## Coverage snapshot

- Source registrations: **184**
- Unique source endpoint/records: **125**
- Source-bearing workspaces/inventories: **44**
- Machine-readable registrations: **101**
- Implemented/discovery/configuration-gated registrations: **66**
- LIVE registrations: **46**
- DISCOVERY registrations: **8**
- AUTH_REQUIRED registrations: **12**
- Registered but not retrieved: **45**
- Stale implemented connectors: **0**

## Integrity boundaries

Missing upstream values remain missing. Statistical periods, versions, units, status/revision metadata, and footnotes remain attached to evidence. A national statistical indicator is not silently converted into a real-time operational condition, health-causation finding, forecast, or legal conclusion.
