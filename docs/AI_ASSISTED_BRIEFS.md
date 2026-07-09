# AI-Assisted Intelligence Briefs

v0.8.2 keeps AI assistance optional and disabled by default. Deterministic fallback briefs remain available even when no AI provider is configured.

## Public Dashboard Brief stability

`[sc_ai_public_dashboard_brief]` renders a local deterministic public-safe brief by default. This avoids gateway errors from Render, Bluehost, Cloudflare, external connectors, or an AI provider.

Use live mode only for private testing:

```text
[sc_ai_public_dashboard_brief live="true"]
```

The public-dashboard backend route defaults to deterministic mode:

```text
/ai/briefs/public-dashboard
```

Use explicit AI only for private testing:

```text
/ai/briefs/public-dashboard?use_ai=true
```
