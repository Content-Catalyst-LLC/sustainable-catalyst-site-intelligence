# Site Intelligence v4.50.0 — Global Source Federation & Regional Authority Registry

v4.50.0 adds a first-class source-authority and federation control plane over the existing Site Intelligence connector ecosystem.

## What changed

- Adds `global_source_federation_registry_v4500.json` with 24 registered source authorities, 10 authority classes, and 7 regional groups.
- Adds 10 modular FastAPI routes under `/public/source-federation`.
- Adds machine-readable source identity, jurisdiction/region scope, domains, languages, federation mode, authority class, and quality status.
- Reuses existing v4.35 jurisdiction-aware precedence rules instead of replacing them.
- Adds deterministic source selection ordered by semantic compatibility, declared jurisdiction precedence, jurisdiction specificity, authority class, freshness, record status, and stable source ID.
- Keeps source authority, quality signals, and caller/user trust choices explicitly separate.
- Adds preview-only federation plans: no automatic remote fetch, import, or remote write occurs.
- Promotes the standalone `Sources` navigation item to the new first-class capability.
- Retains v4.46 spatial evidence, v4.47 spatiotemporal analysis, v4.48 graph relationships, and v4.49 live event fusion.
- Retains WordPress as a thin shell/embed bridge and preserves the 72-shortcode compatibility ceiling.
- Extends the corrected Contabo deployment contract from 31 to 32 release-bound static files.

## Runtime inventory

- Version: 4.50.0
- Capability registry generation: 1.7.0
- Routes: 1409
- Modularized routes: 100
- Capability families: 21
- Source-federation routes: 10/10 modular
- Unclassified routes: 0
- Duplicate method/path contracts: 0

## Interpretation boundary

A source can be authoritative only within its actual jurisdiction, domain, and published scope. A higher authority class cannot substitute for semantic incompatibility. User trust preferences can filter source eligibility, but they do not alter recorded authority class, quality status, provenance, or source identity.
