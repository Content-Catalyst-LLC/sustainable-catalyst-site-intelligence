# Site Intelligence v1.0.0 — Public Flagship Release

This release is the public-launch hardening layer for Sustainable Catalyst Site Intelligence.

## Public page shortcode

```text
[sc_site_intelligence_public_flagship]
```

Use this for the public-facing flagship dashboard page.

## Private release review shortcode

```text
[sc_site_intelligence_release_status]
```

Keep this on private/admin review pages.

## Release endpoints

- `/release/status` — private/admin release status and launch notes
- `/release/checklist` — private/admin launch checklist
- `/release/smoke-test` — private/admin post-deploy smoke-test map
- `/release/public-summary` — public-safe release summary and metadata

## Launch checks

1. Deploy the v1.0.0 backend to Render.
2. Confirm the root endpoint returns version 1.0.0.
3. Install the v1.0.0 WordPress plugin ZIP.
4. Clear WordPress and Cloudflare cache.
5. Place `[sc_site_intelligence_public_flagship]` on the public dashboard page.
6. Confirm no private/admin/report/AI/Search Console/GA4 shortcodes are present on the public page.
7. Test the page logged out or in an incognito browser.
8. Add the suggested page title, excerpt, and meta description.

## Boundary note

Site Intelligence is educational and informational. It does not provide legal, financial, medical, engineering, climate-risk, ESG, assurance, compliance, tax, or investment advice.
