# v3.19.0 — Registry Governance, Challenges, Revocation, and Appeals

This increment adds an append-only governance layer above the federated preservation registry.

## Workflow

1. A public-safe evidence challenge is prepared against an approved, suspended, or revoked institution.
2. A separate reviewer evaluates the evidence and recommends no action, trust-profile change, suspension, or revocation.
3. A separate governor approves the final resolution.
4. A suspended or revoked institution may submit an appeal supported by new public-safe evidence.
5. A separately reviewed and approved appeal may uphold the decision, reinstate the institution, or reinstate it under a modified trust profile.

Every status transition appends a new institutional state. Previous registry records, attestations, exchange packages, and governance events remain retained.

## Public boundary

Only explicitly public, resolved challenges and appeals are published. Actor identities, credentials, internal notes, private disputes, and draft reviews are excluded.

## Authority boundary

Site Intelligence performs no automatic suspension, revocation, reinstatement, network verification, destination write, remote-system enforcement, deletion, or certification.
