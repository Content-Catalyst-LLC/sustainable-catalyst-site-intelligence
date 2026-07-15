# Sustainable Catalyst Site Intelligence v2.3.0

## International Law and Global Governance Observatory

Site Intelligence v2.3.0 adds a dedicated public workspace for official international-law and global-governance records delivered through Sustainable Catalyst Core.

### Public workspace

- Route: `/app/?view=law`
- WordPress shortcode: `[sc_international_law_governance_observatory height="1350"]`

### New capabilities

- Official legal and governance record discovery
- Authority and record-type filters
- Legal body and issuing body context
- Official UN and court document symbols
- Procedural-status preservation
- Adoption and publication dates
- Country and subject associations
- Official citations and canonical source links
- Geographic country-association map
- Chronological legal and governance timeline
- Country legal profile
- Authority matrix
- CSV export and shareable URLs
- Saved View support
- Workbench and Decision Studio handoffs

### Public endpoints

- `GET /public/international-law-observatory`
- `GET /public/international-law-observatory/records`
- `GET /public/international-law-observatory/facets`
- `GET /public/international-law-observatory/timeline`
- `GET /public/international-law-observatory/country-profile`
- `GET /public/international-law-observatory/authority-matrix`
- `GET /public/international-law-observatory/brief`
- `GET /public/international-law-observatory/diagnostics`

### Legal and governance safeguards

- Authority categories remain distinct and are never flattened into a universal legal score.
- A document symbol alone is not treated as proof that a record is binding.
- The application does not make compliance determinations.
- The application does not provide legal advice.
- Core credentials remain server-side and are not delivered to browser JavaScript.
- When Core is unavailable, the workspace reports an explicit disabled, unavailable, degraded, or stale state and does not fabricate records.

### Infrastructure boundary

The release adds no paid provider requirement. It consumes records from the free-source international-law connector layer in Sustainable Catalyst Core. Platform Core remains optional for public Site Intelligence deployment.

### Compatibility

- Recommended Sustainable Catalyst Core: v2.8.0
- Minimum Core for international-law records: v2.7.1
- WordPress plugin: v2.3.0
- Public API schema: v2.0
