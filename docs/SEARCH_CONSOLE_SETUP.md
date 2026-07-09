# Search Console Setup

Site Intelligence v0.3.0+ adds Search Console and SEO Intelligence.

## Required setup

1. Keep the existing Google service-account JSON configured in Render.
2. Add the service-account email to the Sustainable Catalyst Search Console property.
3. Set the exact Search Console property URL in Render.

## Render variables

```text
SC_SI_SEARCH_CONSOLE_LIVE=true
SC_SI_SEARCH_CONSOLE_SITE_URL=https://sustainablecatalyst.com/
SC_SI_SEARCH_CONSOLE_MAX_ROWS=250
SC_SI_SEARCH_CONSOLE_TIMEOUT_SECONDS=10
```

Use the exact property form you see in Search Console. If your verified property is a domain property, use:

```text
SC_SI_SEARCH_CONSOLE_SITE_URL=sc-domain:sustainablecatalyst.com
```

## Diagnostics

```bash
curl -H "X-SC-Intelligence-Token: YOUR_TOKEN" \
"https://sustainable-catalyst-site-intelligence.onrender.com/search/health"
```

If Search Console is unavailable, the dashboard uses sample search data so the WordPress page does not fail.
