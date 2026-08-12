# Site Intelligence v4.35.22 — Palestine Data Federation & Wikimedia Knowledge Context

## Release objective
Extend the v4.35.20 Palestine linked-record recovery into a source-separated country-data federation while adding Wikimedia as a non-authoritative knowledge-context layer. The release must improve discovery and entity context without allowing community-curated context, public attention, or dataset metadata to overwrite source-governed Truth.

## Delivered
- Added a Palestine Open Data Portal CKAN discovery connector and a Palestine-specific federation surface.
- Preserved PCBS as the primary official statistical authority for supported exact concepts.
- Preserved HDX HAPI as a standardized humanitarian-indicator lane and HDX CKAN as humanitarian dataset discovery.
- Preserved World Bank as harmonized international comparison rather than operational current-state authority.
- Added Wikidata entity search/entity resolution for linked identifiers, labels, descriptions, aliases, sitelinks, and claims.
- Added Wikipedia background context through the MediaWiki API.
- Added Wikimedia Commons media discovery with machine-readable licensing/provenance metadata.
- Added Wikimedia Pageviews as a separately labeled public-attention signal.
- Added a lazy, non-blocking country Knowledge Context panel; Wikimedia failure does not hold open the core country workspace.
- Added explicit `truth_precedence: excluded` handling for Wikimedia context.
- Added deterministic, network-free readiness surfaces for the Palestine federation and Wikimedia Knowledge Context.
- Added a split-mode v4.35.22 browser verifier so desktop, mobile, and iframe can be validated independently without depending on optional upstream timing.

## Palestine source roles
- **PCBS** — PRIMARY OFFICIAL STATISTICS
- **Palestine Open Data Portal** — OFFICIAL DATASET DISCOVERY
- **HDX HAPI** — STANDARDIZED HUMANITARIAN INDICATORS
- **HDX CKAN** — HUMANITARIAN DATASET DISCOVERY
- **World Bank** — HARMONIZED INTERNATIONAL COMPARISON
- **Wikimedia** — KNOWLEDGE CONTEXT; EXCLUDED FROM TRUTH PRECEDENCE

## Evidence boundaries
- Dataset discovery is not an operational observation.
- Wikimedia content is community-curated context and cannot override official statistics, scientific measurements, or humanitarian operational reporting.
- Pageviews measure attention to Wikimedia content, not severity, importance, prevalence, opinion, humanitarian need, or causality.
- Commons media remain subject to the license and attribution metadata attached to each file.
- A failed or unavailable Wikimedia request cannot invalidate an otherwise healthy Site Intelligence release.

## Verification
- Deterministic pytest suite: **1,629 / 1,629 passed**.
- Browser workspace gate: **35/35 desktop, 35/35 mobile, 35/35 iframe; zero degraded routes**.
- Existing first-party experience budgets retained; no budget increase was used for this feature.
- Release readiness remains deterministic and network-free; live external-provider health remains non-blocking.
