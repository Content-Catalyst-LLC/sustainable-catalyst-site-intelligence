# Public Dashboard Visual QA and Copy Polish

Version: 0.10.1

This release adds a private/review layer for final public dashboard QA before public promotion.

## Endpoint

- `/public/page-builder/visual-qa`

## WordPress shortcode

- `[sc_public_dashboard_visual_qa]`

Use this shortcode on an internal review page, not the public dashboard page.

## Public page recommendation

Use this shortcode for the public flagship page:

```text
[sc_site_intelligence_public_flagship]
```

The QA layer checks hero clarity, non-advice boundaries, module order, mobile spacing, empty/error states, and public/private shortcode separation.
