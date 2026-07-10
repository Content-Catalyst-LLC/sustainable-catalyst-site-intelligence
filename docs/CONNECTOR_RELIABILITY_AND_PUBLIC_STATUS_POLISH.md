# Site Intelligence v1.3.1 — Connector Reliability Patch and Public Status Polish

This patch builds on the v1.3.0 live connector status layer by adding public-facing reliability labels, status-card payloads, cache-state labels, freshness-state labels, and recovery guidance.

## Public endpoints

```text
/public/connectors/reliability
/public/connectors/status-polish
```

These endpoints complement the v1.3.0 endpoints:

```text
/public/connectors/status
/public/connectors/cache
/public/connectors/freshness
/public/connectors/world-bank
/public/connectors/openalex
/public/connectors/crossref
/public/connectors/github
/public/connectors/environmental
```

## WordPress shortcodes

```text
[sc_public_connector_reliability]
[sc_public_connector_status_polish]
```

Recommended page placement:

```text
/platform/site-intelligence/source-health/
  [sc_public_connector_status]
  [sc_public_connector_reliability]

/platform/site-intelligence/source-methodology/
  [sc_public_cache_status]
  [sc_public_source_freshness]
  [sc_public_connector_status_polish]
```

## Reliability labels

```text
healthy       Public panel can show a stable live-or-cached or cached summary.
degraded      Public panel should stay conservative and show clear limits.
fallback_safe Public panel should prefer fallback summaries and methodology notes.
planned       Public panel is documented but should not imply live availability.
```

## Public/private boundary

Public connector panels must never expose:

```text
API key values
service account JSON
raw upstream payloads
request/response headers
backend logs
private analytics
secret scan details
```

## Interpretation

Reliability labels are public display guidance. They are not uptime guarantees, certification, professional assurance, regulatory findings, or compliance determinations.
