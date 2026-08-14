# Site Intelligence v4.35.25 — Country Intelligence Presentation Audit

## Release objective

Make multi-source country intelligence legible as an evidence hierarchy rather than a flat statistics dashboard.

## Evidence hierarchy

1. **Conditions Now** — dated operational/humanitarian reporting. Absence of returned records is not interpreted as normal conditions.
2. **Primary / sector official evidence** — national statistical authorities and responsible sector authorities for compatible concepts.
3. **Published/intergovernmental evidence** — source-aware public observations with method, geography, and reference period preserved.
4. **Harmonized benchmark** — standardized international comparison series such as World Bank indicators.
5. **Knowledge context** — contextual sources remain outside Truth precedence.

## Semantic guards

- Transport state (`live`, cached, stale) cannot upgrade an observation's evidence authority.
- Annual electricity-access percentages cannot establish present service continuity.
- Annual drinking-water-access percentages cannot establish present service continuity or water quality.
- Operational and structural observations are not automatically averaged or blended.
- Gaza, West Bank, and Palestine-wide observations retain their geographic scopes.
- Source disagreements remain visible through the inherited v4.35.22 reconciliation layer.

## UI contract

The Country workspace exposes:

- Country Intelligence Brief
- evidence status and authority summary
- Conditions Now boundary
- source-role cards
- official/published/comparative indicator section
- interpretation text on structural access metrics
- evidence-detail controls
- source-aware reconciliation output

## Release health

`/public/country-evidence-presentation/readiness` is deterministic and network-free. External-provider availability is not a release blocker. Promotion requires the presentation-semantic checks through `/public/deployment-verification`.

## Validation evidence

- Deterministic suite: 1,657 passed / 0 failed.
- Targeted country/evidence regression slice: 54/54 passed.
- Country presentation browser regression: PASS.
- Palestine/Israel hostile-catalog browser regression: PASS.
- Workspace browser control plane: desktop 35/35; mobile 35/35; iframe 35/35; zero degraded.
- JSON/GeoJSON parsing: 135 files.
- JavaScript validation: 152 files.
- PHP syntax: PASS.
- Static security findings: 0.
