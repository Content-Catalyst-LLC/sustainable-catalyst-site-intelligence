# Site Intelligence v2.3.0 — International Law and Global Governance Observatory

## Purpose

This release adds a public research workspace for official international-law and global-governance records delivered through Sustainable Catalyst Core. It is designed for source discovery, comparative orientation, chronology, country-level research, and evidence-aware handoffs—not legal advice or automated legal conclusions.

## Public interface

- Route: `/app/?view=law`
- WordPress shortcode: `[sc_international_law_governance_observatory height="1350"]`

## Public endpoints

- `GET /public/international-law-observatory`
- `GET /public/international-law-observatory/records`
- `GET /public/international-law-observatory/facets`
- `GET /public/international-law-observatory/timeline`
- `GET /public/international-law-observatory/country-profile`
- `GET /public/international-law-observatory/authority-matrix`
- `GET /public/international-law-observatory/brief`
- `GET /public/international-law-observatory/diagnostics`

## Preserved legal context

The bridge retains record type, authority category, issuing body, legal body, official symbol, procedural status, adoption and publication dates, countries, subjects, languages, related instruments, related cases, related resolutions, related SDG targets, citation, canonical source, license, attribution, and retrieval context when supplied by Core.

Authority categories remain distinct. A treaty, judgment, advisory opinion, Security Council resolution, General Assembly resolution, human-rights recommendation, ILC text, and official report are not treated as legally equivalent.

## Safeguards

- No legal advice or compliance determination.
- No automatic claim that a record is binding.
- No document-symbol-only inference of legal effect.
- No Core credential exposure to browser code.
- No fabricated fallback records.
- Public query values and returned URLs are sanitized.
- Disabled, unavailable, degraded, stale, and connected states remain visible.

## Free-service boundary

This release adds no paid API requirement. It consumes records from the free-source connector layer in Sustainable Catalyst Core. Core remains optional for Site Intelligence deployment; when it is not configured, the law workspace remains visible with an explicit unavailable state.
