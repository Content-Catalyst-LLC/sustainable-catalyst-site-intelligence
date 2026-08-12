# Site Intelligence v4.35.23 — Country Identity & Selector Routing Audit

## Defect

Observed UI behavior:

- scrolling/selecting **Israel** could leave or open the **Palestine** profile;
- selecting **Palestine** could fail to visibly commit to Palestine.

This was treated as a country-identity/routing defect, not a data-source dispute.

## Root cause

The country selector, backend country resolver, and cartographic focus did not share one canonical country identity plane.

The selector could be hydrated from the bundled Data Truth country catalog while the map/backend still depended on `/public/countries`, which could be populated by a live World Bank country catalog. A partial, stale, slow, or unavailable live catalog could therefore make an ISO3 value selectable while the downstream resolver lacked the same identity. The previous country state could remain visible and look like a cross-country redirect.

## Repair

### Canonical identity plane

`backend/data/country_identity_registry_v43523.json` is now the first-party country identity source. Runtime providers may enrich metadata but cannot replace the canonical ISO3/ISO2/name binding.

Required bindings:

- `ISR` / `IL` / `Israel`
- `PSE` / `PS` / `Palestine`

Palestine aliases include `State of Palestine`, `Palestinian Territories`, `Palestinian Territory`, and `West Bank and Gaza`, but none resolves to `ISR`.

### Backend resolution

`live_country_intelligence.py` now starts from the canonical registry and enriches field-by-field from live metadata. If upstream catalog retrieval fails, the full first-party catalog remains resolvable.

### Data Truth and map focus

Data Truth and cartographic focus use the same canonical registry/catalog. Map focus no longer depends on a live country-list provider to resolve a selection.

### UI commit and identity guard

The selected ISO3 is committed to route state before optional indicator retrieval begins. Overview and trend payloads must return the same ISO3 as the request; otherwise rendering is blocked with an identity mismatch state.

### Release gate

`/public/country-identity/readiness` verifies the first-party registry, country count, ISR/PSE bindings, network-free readiness, and non-blocking upstream policy. The deployment-verification contract requires that readiness plane.

## Regression cases

The deterministic browser regression covers:

1. direct `PSE` selection → Palestine;
2. direct `ISR` selection → Israel;
3. rapid `PSE` then `ISR` → final Israel;
4. rapid `ISR` then `PSE` → final Palestine;
5. backend identity resolution during upstream catalog failure;
6. country search isolation between Israel and Palestine;
7. first-party readiness contract;
8. deployment-gate identity contract.
