# Site Intelligence v4.10.0 — Monitoring, Digests, and Early-Warning Operations

## Purpose

v4.10.0 turns the existing Alerts and Scheduled Monitoring capabilities into a coherent review-oriented monitoring layer. It adds explicit watchlists, geographic monitoring areas, source-change checks, threshold evaluation, alert-state transitions, modeled-warning separation, draft digest generation, and reviewed-feed contracts without claiming automatic emergency response or autonomous publication.

## Public contracts

- `GET /public/monitoring-operations`
- `POST /public/monitoring-operations/watchlist/preview`
- `POST /public/monitoring-operations/evaluate`
- `POST /public/monitoring-operations/source-changes`
- `POST /public/monitoring-operations/modeled-warning/preview`
- `POST /public/monitoring-operations/digest/preview`
- `GET /public/monitoring-operations/feed-contract`

## Operational behavior

- Watchlists preserve countries, public geographic areas, source IDs, cadence, and explicit threshold rules.
- Alert histories use `new`, `continuing`, `changed`, `resolved`, and `withdrawn` states.
- Every threshold alert exposes the rule, public signal, trigger explanation, freshness state, and limitations.
- `resolved` is explicitly evaluation-relative and never presented as proof that a real-world condition ended.
- Source-change monitoring distinguishes platform-observed change from a verified publisher-wide outage.
- Modeled warnings are kept separate from source alerts and never presented as emergency instructions, probabilities, or automatic actions.
- Digests remain `draft` and `publication_allowed=false` until a separate human review process approves publication.
- Public feed contracts support JSON, Atom, and RSS without requiring subscriber profiles or tracking.

## Governance boundaries

v4.10.0 does not provide automatic emergency dispatch, individual tracking, hidden risk scoring, automatic consequential action, fabricated events, or automatic publication.

## Compatibility

The release preserves v3.27.0 Research Evidence and Knowledge Integration, v3.26.0 assurance contracts, unified cross-view state, Global Data Truth, record provenance, the 173-country selector, loading recovery, production soak, service-worker closure, and fixed WordPress embed isolation.
