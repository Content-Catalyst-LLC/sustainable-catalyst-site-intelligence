# v3.27.0 Research Evidence and Knowledge Integration Audit

## Integration targets

Site Intelligence prepares public-safe, portable handoff previews for four targets: Research Librarian, Knowledge Library, Workbench, and Decision Studio.

## Provenance contract

Each normalized evidence record retains a source snapshot, observation/retrieval dates, truth state, limitations, and a deterministic SHA-256 fingerprint. Evidence manifests retain these fields rather than flattening records into unsupported summaries.

## Knowledge boundary

Knowledge Library discovery returns a query plan with `match_state: not-executed` and an empty verified-match set until a real library index performs the search. No inferred or fabricated document match is returned.

## Human control

Every handoff packet declares `preview_only: true`, `delivery_attempted: false`, `delivery_verified: false`, `human_confirmation_required: true`, and `publication_allowed: false`.

## Claim mapping

Claim/evidence relationships preserve support, contradiction, qualification, and context. The system does not automatically resolve contested claims.
