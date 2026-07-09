# AI-Assisted Intelligence Briefs

Site Intelligence v0.8.0 adds an AI-assisted brief layer over the structured report generator.

## Safety model

The AI provider is disabled by default. Every brief endpoint can produce a deterministic fallback brief without any external model call. Optional model output is treated as an interpretation layer over structured Site Intelligence reports, not as a source of truth.

## Endpoints

```text
/ai/status
/ai/briefs/site-intelligence
/ai/briefs/search
/ai/briefs/publishing
/ai/briefs/external-sources
/ai/briefs/public-dashboard
/intelligence/ai-briefs
```

All endpoints are protected by the existing Site Intelligence token.

## Parameters

```text
mode=private|public
use_ai=true|false
format=json|markdown
```

`mode=public` returns a public-safe summary orientation, but the output should still be reviewed before publication.

## Optional Gemini configuration

```text
SC_SI_AI_PROVIDER=gemini
SC_SI_GEMINI_API_KEY=<render-secret>
SC_SI_GEMINI_MODEL=gemini-1.5-flash
SC_SI_AI_TEMPERATURE=0.2
SC_SI_AI_MAX_OUTPUT_TOKENS=1200
SC_SI_AI_TIMEOUT_SECONDS=12
```

Do not place model keys in WordPress content or shortcode attributes.
