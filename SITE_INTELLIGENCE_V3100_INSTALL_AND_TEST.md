# Site Intelligence v3.10.0 — Install and Test

## Install

1. Unzip the release bundle in `~/Downloads`.
2. Run `chmod +x install_and_push_site_intelligence_v3_10_0.sh`.
3. Run `./install_and_push_site_intelligence_v3_10_0.sh`.
4. Deploy the latest `main` commit in Render using **Clear build cache & deploy**.
5. Upload `sustainable-catalyst-site-intelligence-v3.10.0-wordpress.zip` in WordPress.

## Public verification

- `/public/build-info` reports backend version `3.10.0`.
- `/public/live-intelligence/briefings/policy` reports no automatic publication, no automatic WordPress write, and required human review.
- `/public/live-intelligence/briefings/templates` lists the five bounded briefing types.
- `/public/live-intelligence/briefings` returns only approved public briefings.
- Public JSON and Markdown exports retain source-linked claims and limitations.

## WordPress shortcode

```text
[sc_live_intelligence_briefings]
```

## Editorial workflow

1. Create a private briefing draft from canonical signals, reviewed alerts, or approved digests.
2. Review every claim, source, timestamp, freshness state, geography, and limitation.
3. Approve or reject the draft with an identified reviewer and documented reason.
4. Only an approved public briefing appears on public routes or the WordPress shortcode.
5. Export JSON or Markdown, or create a provider-neutral handoff.
6. Complete publication in the Knowledge Library, Publications, Decision Studio, or WordPress through the receiving system or a human editor.
