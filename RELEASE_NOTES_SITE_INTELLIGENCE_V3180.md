# Site Intelligence v3.21.0 — Federated Preservation Registry, Trust Profiles, and Cross-Institution Verification

## Summary

v3.21.0 adds a public-safe institutional preservation registry above the approved exchange workflow introduced in v3.17.0. It records evidence-linked institution profiles, checksum-bound attestations, and unique-institution consensus summaries without treating registry presence as accreditation, certification, ranking, or endorsement.

## Delivered

- Prepared, verified, and approved institutional registry entries.
- Public references for repository services and preservation policies.
- Supported exchange profiles and verification methods per institution.
- Evidence-linked trust profiles: declared, policy reviewed, and verified exchange partner.
- Human-reported attestations bound to approved exchange-package SHA-256 checksums.
- multi-party consensus that counts each approved institution once.
- Configurable consensus threshold, defaulting to two institutions.
- JSON and Markdown institution and consensus packages.
- Read-only public API and WordPress registry surfaces.
- Append-only event history for institution and attestation governance.

## Boundaries

- No certification, accreditation, ranking, or endorsement claim.
- No network verification.
- No remote deposit or destination write.
- No archive or source-record mutation.
- No credential, recipient, subscriber, or personal-contact storage.
- No external system receives write authority.

## WordPress shortcode

`[sc_live_intelligence_preservation_registry]`
