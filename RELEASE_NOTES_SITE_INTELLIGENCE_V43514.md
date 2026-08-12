# Site Intelligence v4.35.14 — High-Priority Workspace Connector Closure IV: Agriculture, Food Security & Humanitarian Conditions

## Release objective
Close the ambiguous machine-interface backlog in Agriculture, Crops & Food Systems and Humanitarian Intelligence while preserving source semantics, provenance, bounded retrieval, configuration truth, and non-blocking external source health.

## Added / normalized interfaces
- GDACS Events API — LIVE public bounded event retrieval.
- HDX CKAN — DISCOVERY for public humanitarian dataset metadata.
- HDX HAPI — AUTH_REQUIRED via `SC_SI_HDX_HAPI_APP_IDENTIFIER`.
- IPC API — AUTH_REQUIRED via `SC_SI_IPC_API_KEY`.
- FEWS NET Data Warehouse — LIVE public bounded retrieval for market prices, trade, acute food insecurity classifications, and population estimates.
- ReliefWeb V2 duplicate registry row normalized to AUTH_REQUIRED via `SC_SI_RELIEFWEB_APPNAME`.

## Integrity boundaries
GDACS alerts are not national emergency instructions. HDX discovery metadata is not a current humanitarian-condition observation. HDX HAPI standardizes upstream indicators without creating a new Site Intelligence classification. IPC phases remain IPC-issued classifications for defined periods and geographies. FEWS NET projections remain projections and are not silently relabeled as observations or IPC-issued classifications. Missing upstream values remain missing.

## Closure outcome
Agriculture, Crops & Food Systems REGISTERED machine-interface backlog: 0.
Humanitarian Intelligence REGISTERED machine-interface backlog: 0.

Machine-readable audit: 112 registrations; LIVE 48; DISCOVERY 13; AUTH_REQUIRED 17; REGISTERED-not-retrieved 32; BULK 2; STALE 0. Public connector catalog: 45 interfaces — 28 LIVE, 9 DISCOVERY, 8 AUTH_REQUIRED.

## Validation
1,553 deterministic tests passed. 134 JSON/GeoJSON files parsed. 151 JavaScript files syntax-validated. WordPress PHP syntax passed. Static security scan returned 0 findings.
