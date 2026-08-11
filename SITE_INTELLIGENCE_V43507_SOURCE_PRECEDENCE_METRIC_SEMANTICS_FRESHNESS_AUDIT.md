# v4.35.12 Evidence Intelligence Audit

## Release objective

Prevent Site Intelligence from selecting a source merely because it is fresher, more convenient, or internationally standardized when it does not answer the requested evidence question.

## Selection order

1. Metric concept must be an exact semantic match.
2. Unit must be compatible with the requested concept.
3. Jurisdiction-specific source precedence is applied when defined.
4. Authority class is considered.
5. Publication cadence determines freshness interpretation.
6. Provider status such as final, approved, revised, provisional, or estimated is retained.
7. Missing values remain missing.
8. Conflicting exact-concept observations are disclosed rather than blended.

## Palestine electricity case

### Structural electricity access

Concept: `electricity_structural_access`

Preferred evidence order for Palestine:

1. Palestinian Central Bureau of Statistics PxWeb when a compatible official observation exists.
2. World Bank as harmonized fallback/comparison evidence.

This metric can support a statement about the share of population classified as having electricity access for a disclosed reference period.

It cannot support a claim about current electricity availability, grid reliability, outage status, hours supplied, generator dependence, or current service continuity.

### Operational electricity availability

Concept: `electricity_operational_availability`

Preferred source families include grid/operator, Palestinian energy-authority, and OCHA/ReliefWeb operational evidence. World Bank access data is semantically ineligible for this question.

## Freshness

Freshness is relative to expected publication cadence. An annual official statistic can remain current evidence for its concept while being months old. A near-real-time operational record can become stale after days. Freshness cannot convert a wrong metric into an eligible one.

## Conflict handling

When two exact-concept observations have the same unit and observation period but materially disagree, Site Intelligence emits a conflict record and retains both values. It does not average them automatically.

## Deployment boundary

Evidence readiness is deterministic and network-free. External API availability remains operational source health and is not a release blocker.
