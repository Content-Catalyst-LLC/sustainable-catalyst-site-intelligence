# Site Intelligence v3.9.0 — Install and Test

## Install

1. Unzip the release bundle in `~/Downloads`.
2. Run `chmod +x install_and_push_site_intelligence_v3_9_0.sh`.
3. Run `./install_and_push_site_intelligence_v3_9_0.sh`.
4. Deploy the latest `main` commit in Render with **Clear build cache & deploy**.
5. Upload `sustainable-catalyst-site-intelligence-v3.9.0-wordpress.zip` in WordPress.

## Public verification

- `/public/build-info` reports backend version `3.9.0`.
- `/public/live-intelligence/subscriptions/policy` reports no profile storage, direct email, webhook delivery, automatic publication, or emergency authority.
- `/public/live-intelligence/subscriptions/catalog` returns only approved public watchlists.
- `/public/live-intelligence/subscriptions/alerts` returns only approved public alerts.
- `/public/live-intelligence/subscriptions/digests` returns only approved public digests.

## WordPress shortcodes

```text
[sc_live_intelligence_watchlists]
[sc_live_intelligence_alerts]
[sc_live_intelligence_digests]
```

## Administrative workflow

1. Create a private watchlist first.
2. Review its scope and rules.
3. Public visibility requires `human_approved=true`, `approved_by`, and `approval_reason`.
4. Evaluate manually before enabling a cadence.
5. Review every alert before public publication.
6. Build and review a digest before creating a provider-neutral handoff.
7. Pass approved handoffs to Catalyst Communications or another consent-aware delivery system; Site Intelligence does not store recipients or perform delivery.
