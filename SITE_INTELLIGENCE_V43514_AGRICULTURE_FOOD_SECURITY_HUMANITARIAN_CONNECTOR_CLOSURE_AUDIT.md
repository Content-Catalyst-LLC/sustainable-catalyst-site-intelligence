# Site Intelligence v4.35.15 — Agriculture, Food Security & Humanitarian Connector Closure Audit

## Purpose
Advance the “simply works” milestone by closing ambiguous machine-interface registrations in Agriculture/Food Security and Humanitarian Intelligence and replacing them with implemented LIVE, DISCOVERY, or explicit AUTH_REQUIRED states.

## Closure IV interfaces

### GDACS Events API — LIVE
Authority: Global Disaster Alert and Coordination System / EC-JRC.
Controls: bounded event type, alert level, and result limit. GDACS alerts and impact models remain source-defined and do not become Sustainable Catalyst emergency instructions.

### HDX CKAN dataset discovery — DISCOVERY
Authority: OCHA Centre for Humanitarian Data / Humanitarian Data Exchange.
Controls: non-empty bounded search and capped results. Dataset metadata/discovery is not treated as a verified present humanitarian condition.

### HDX HAPI — AUTH_REQUIRED
Configuration: `SC_SI_HDX_HAPI_APP_IDENTIFIER`.
Controls: allowlisted food-security / food-price themes, bounded pagination, credential redaction. HAPI-standardized observations retain source/resource metadata and do not become a new Site Intelligence classification.

### IPC API — AUTH_REQUIRED
Configuration: `SC_SI_IPC_API_KEY`.
Controls: allowlisted resources and bounded country/year/analysis filters; credential redaction. Site Intelligence preserves IPC classifications and does not create, upgrade, downgrade, average, or synthesize IPC phases.

### FEWS NET Data Warehouse — LIVE
Authority: FEWS NET.
Controls: allowlisted food-security phase, food-insecure population, market-price, and cross-border-trade datasets; requires bounded geography/date/scenario context; capped page size. Projections remain projections and are not silently relabeled as observations or IPC-issued classifications.

### ReliefWeb V2 normalization — AUTH_REQUIRED
The duplicate ReliefWeb registry row now matches the existing V2 connector truth: approved `appname` configuration is required. No obsolete V1/ambiguous REGISTERED state remains for this row.

## Production audit
- Source registrations: 191
- Unique endpoint/source records: 129
- Source-bearing workspaces: 44
- Machine-readable registrations: 112
- LIVE: 48
- DISCOVERY: 13
- AUTH_REQUIRED: 17
- REGISTERED / not retrieved: 32
- BULK: 2
- STALE: 0
- Implemented / discovery / configuration-gated: 78

## Target workspace closure
Agriculture, Crops & Food Systems: 4 machine-readable registrations; LIVE 2, AUTH_REQUIRED 2, REGISTERED 0.
Humanitarian Intelligence: 5 machine-readable registrations; REGISTERED 0, with public LIVE paths available without credentials.

## Deployment boundary
External provider availability remains operational source health and never blocks a valid release identity/runtime/route/evidence deployment gate. Readiness endpoints remain deterministic and network-free.
