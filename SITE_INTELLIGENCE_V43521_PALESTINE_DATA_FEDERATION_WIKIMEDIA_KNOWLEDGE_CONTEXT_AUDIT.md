# Site Intelligence v4.35.22 — Palestine Data Federation & Wikimedia Knowledge Context Audit

## Architecture decision
v4.35.22 separates four questions that must not collapse into a single generic “source” state:

1. What is the authoritative statistic?
2. What official or humanitarian datasets are discoverable?
3. What operational/humanitarian indicators are available?
4. What contextual knowledge helps a user understand the selected entity?

The first three belong to evidence federation. The fourth belongs to knowledge context. Wikimedia is intentionally confined to the fourth role.

## Palestine Data Federation
`palestine_data_federation_v43521.py` composes source lanes for `PSE` while retaining their distinct semantics:

- PCBS: primary official statistical authority for supported exact concepts.
- Palestine Open Data Portal: official CKAN dataset discovery.
- HDX HAPI: standardized humanitarian indicators when configured.
- HDX CKAN: humanitarian dataset discovery.
- World Bank: harmonized comparison/fallback, not operational present-tense truth.

The federation response exposes source roles and limitations instead of silently selecting or blending incompatible records.

## Palestine Open Data recovery
`authoritative_connectors_v43521.py` adds a public CKAN discovery connector for the Palestine Open Data Portal. `country_linked_records_v43520.py` can retain explicitly country-scoped official dataset-discovery records for Palestine while keeping them separate from operational events/reports.

## Wikimedia Knowledge Context
`wikimedia_knowledge_context_v43521.py` provides four bounded lanes:

### Wikidata
Entity search and entity retrieval provide linked identifiers, labels, descriptions, aliases, sitelinks, and claims. These are entity-resolution/context data, not measurement authority.

### Wikipedia
Introductory page context is retrieved as background text. It remains community-curated background and is never admitted into statistical or operational Truth precedence.

### Wikimedia Commons
Media search retrieves file URL/thumbnail information plus machine-readable extended metadata such as license, artist, and credit where provided upstream. A discovered image does not become evidentiary proof of current conditions.

### Wikimedia Pageviews
Daily pageview totals are retained as a `PUBLIC ATTENTION SIGNAL`. The contract explicitly rejects interpretation as severity, importance, prevalence, opinion, humanitarian need, or causality.

## Country workspace integration
The country workspace dynamically creates a Knowledge Context panel rather than increasing the already tightly bounded base HTML shell. Core country indicators and linked records render independently. Knowledge Context is loaded lazily and is optional; upstream Wikimedia latency or failure cannot block country-workspace usability.

For Palestine, the panel also exposes the Data Federation source-role summary so users can distinguish official statistical authority, official dataset discovery, humanitarian indicators/discovery, international comparison, and community-curated context.

## Truth boundary
The Wikimedia layer reports `truth_precedence: excluded`. Release tests assert that it cannot outrank or overwrite:
- national statistical authorities;
- scientific measurement sources;
- operational humanitarian sources;
- source-governed canonical observations;
- record Truth/evidence fingerprints.

## Performance boundary
The first implementation exceeded the inherited CSS experience budget. The release was tightened by reusing existing country-card primitives rather than raising the budget.

Final measured shell budgets during validation:
- HTML: **171,981 / 172,000 bytes**
- CSS: **101,860 / 102,000 bytes**
- first-party shell total: **481,692 / 500,000 bytes**

## Deterministic verification
- New v4.35.22 feature regressions: 8 dedicated tests.
- Complete inherited + new deterministic suite: **1,629 / 1,629 passed**.
- Browser route visibility: **35/35 desktop, 35/35 mobile, 35/35 iframe**, zero degraded routes.
- Palestine federation and Wikimedia readiness are network-free and external-provider health is non-blocking.

## Scope boundary
This release does not claim that Wikimedia is authoritative, that every Palestine Open Data dataset is current, that HDX discovery metadata describes present conditions, or that every Palestinian ministry/operational authority is already integrated. It creates a disciplined federation and context architecture on which those source-specific integrations can be added without weakening Truth semantics.
