# Sustainable Catalyst Site Intelligence

**Version:** 0.8.2  
**Build:** Public Dashboard Brief Local Fallback Patch

Site Intelligence connects Sustainable Catalyst analytics, registry intelligence, search visibility, publishing priorities, public dashboard summaries, external connectors, report exports, and AI-assisted briefs.

## v0.8.2 patch

v0.8.2 stabilizes the final AI brief shortcode:

```text
[sc_ai_public_dashboard_brief]
```

The Public Dashboard Brief now renders locally by default inside WordPress. This prevents Bluehost, Cloudflare, Render, external connector, or AI-provider gateway errors from affecting the page.

To test the backend route directly from WordPress, opt in explicitly:

```text
[sc_ai_public_dashboard_brief live="true"]
```

For normal dashboard pages, leave `live` off.

## Key behavior

- Default public-dashboard brief is deterministic and public-safe.
- No raw analytics are exposed.
- No external API calls are made by the default shortcode.
- No AI-provider call is made by the default shortcode.
- Raw HTML gateway pages are suppressed.
- Backend endpoint `/ai/briefs/public-dashboard` defaults to `use_ai=false`.

## Deploy check

After pushing and redeploying, test:

```bash
curl "https://sustainable-catalyst-site-intelligence.onrender.com/"
```

Expected version:

```json
{"version":"0.8.2"}
```

Then update the WordPress plugin ZIP and use:

```text
[sc_ai_public_dashboard_brief]
```
