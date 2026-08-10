# Site Intelligence v4.28.0 Energy Infrastructure / Power Systems / Electricity Audit

## Architectural invariants
- Earth Observation extension only; no new top-level route.
- Six primary areas preserved.
- 35 public navigation routes preserved.
- Backend and WordPress energy assets must remain byte-identical.
- Nested backend/backend runtime-state paths are rejected by manifest and verifier.
- Render promotion remains bounded and visible.

## Evidence separation
1. OpenStreetMap: mapping feature, never proof of energization, operating status, safety, ownership or access.
2. EIA: reported/forecast series, with forecast and capability semantics retained.
3. Ember: harmonized statistics, never real-time telemetry or local service evidence.
4. ENTSO-E: market/system publications, retaining bidding-zone/control-area/process semantics; forecast and unavailability records are not platform-issued operational determinations.

## Safety / truth constraints
No automatic outage declaration, reliability violation, grid emergency, equipment-safety finding, retail-price finding, navigation instruction or automatic action is authorized.
