# Site Intelligence v3.9.0 — Signal Subscriptions, Alerts, and Scheduled Intelligence

This release connects the canonical Live Intelligence signal system to governed watchlists, deterministic alert matching, reviewed digests, public feeds, and provider-neutral communications handoffs.

## Delivered

- Public and private watchlists over the existing connected Live Intelligence surfaces.
- Manual, hourly, daily, and weekly evaluation cadences.
- Family, source, freshness, destination, geography, text, and numeric-threshold rules.
- `all` and `any` rule matching with bounded rule and alert limits.
- Duplicate alert suppression based on watchlist, signal, value, freshness, and matched rules.
- Review-pending alerts that cannot become public without an identified human reviewer and reason.
- Human-reviewed public digests.
- Public JSON, RSS, and Atom feeds for approved watchlists and approved alerts.
- Provider-neutral handoff manifests for Catalyst Communications or downloadable delivery workflows.
- Public WordPress panels for watchlists, reviewed alerts, and digests.

## Privacy and governance boundary

Site Intelligence does not store subscriber profiles, email addresses, recipient lists, contact records, IP addresses, cookies, user agents, or session identifiers in this workflow. It does not send email, call webhooks, manage consent, personalize messages, or perform delivery. A separate communications service must manage recipients, consent, unsubscribe controls, and provider delivery.

Public watchlists, alerts, and digests require human approval. The system has no automatic publication or emergency-dispatch authority. A missing alert is not proof that no meaningful real-world change occurred.

## Preserved

- One canonical source and signal system across all Live Intelligence surfaces.
- Explicit freshness and last-known-good boundaries.
- Human-governed rotation and public-value analytics.
- Source lineage, evidence, responsible-use notes, maps, and deeper platform handoffs.
- Reduced-motion, keyboard, mobile, no-JavaScript, and forced-colors behavior.
- Prohibition on sponsored, advertising, and affiliate items inside Live Intelligence.
