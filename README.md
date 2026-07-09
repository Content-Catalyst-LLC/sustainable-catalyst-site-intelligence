# Sustainable Catalyst Site Intelligence

**Version:** 0.8.0  
**Build:** AI-Assisted Intelligence Briefs

Site Intelligence is a custom FastAPI backend and WordPress bridge for Sustainable Catalyst. It combines GA4 analytics, Search Console intelligence, registry/page mapping, event validation, external data connectors, public dashboard summaries, report/export tools, and AI-assisted internal planning briefs.

## v0.8.0 — AI-Assisted Intelligence Briefs

v0.8.0 adds an AI-brief layer on top of the existing report generator. The layer is intentionally safe by default:

- AI provider is disabled unless configured through Render environment variables.
- Deterministic fallback briefs always work without external model calls.
- Brief endpoints are token-protected and intended for internal review.
- Public-dashboard briefs use public-safe dashboard/methodology/readiness inputs.
- Gemini is supported optionally; OpenAI is not required.

## New Backend Endpoints

```text
/ai/status
/ai/briefs/site-intelligence
/ai/briefs/search
/ai/briefs/publishing
/ai/briefs/external-sources
/ai/briefs/public-dashboard
/intelligence/ai-briefs
```

AI brief endpoints support:

```text
mode=private|public
use_ai=true|false
format=json|markdown
```

## New WordPress Shortcodes

```text
[sc_ai_brief_status]
[sc_ai_site_intelligence_brief]
[sc_ai_search_brief]
[sc_ai_publishing_brief]
[sc_ai_external_sources_brief]
[sc_ai_public_dashboard_brief]
```

Recommended internal brief page:

```text
[sc_ai_brief_status]

[sc_ai_site_intelligence_brief]

[sc_ai_search_brief]

[sc_ai_publishing_brief]

[sc_ai_external_sources_brief]

[sc_ai_public_dashboard_brief]
```

## Optional AI Provider Configuration

No new variables are required. Without these, v0.8.0 returns deterministic fallback briefs.

To enable Gemini on Render:

```text
SC_SI_AI_PROVIDER=gemini
SC_SI_GEMINI_API_KEY=<your-gemini-api-key>
SC_SI_GEMINI_MODEL=gemini-1.5-flash
SC_SI_AI_TEMPERATURE=0.2
SC_SI_AI_MAX_OUTPUT_TOKENS=1200
SC_SI_AI_TIMEOUT_SECONDS=12
```

To keep AI disabled explicitly:

```text
SC_SI_AI_PROVIDER=disabled
```

## Existing Core Report Endpoints

```text
/reports/site-intelligence
/reports/search-intelligence
/reports/content-strategy
/reports/external-sources
/reports/climate-energy
/reports/indexing
/reports/export
/intelligence/reports
```

All private report and AI brief endpoints require `X-SC-Intelligence-Token`.

## Required Render Variables

```text
SC_SI_ENVIRONMENT=production
SC_SI_DEMO_MODE=false
SC_SI_API_TOKEN=<private-token>
SC_SI_CORS_ORIGINS=https://sustainablecatalyst.com
SC_SI_GA4_PROPERTY_ID=<numeric-ga4-property-id>
SC_SI_GOOGLE_APPLICATION_CREDENTIALS_JSON=<one-line-service-account-json>
SC_SI_REGISTRY_PATH=backend/data/site_registry.seed.json
SC_SI_SEARCH_CONSOLE_LIVE=true
SC_SI_SEARCH_CONSOLE_SITE_URL=https://sustainablecatalyst.com/
```

Optional external-source variables:

```text
SC_SI_EIA_API_KEY=
SC_SI_EPA_AQS_EMAIL=
SC_SI_EPA_AQS_KEY=
```

## Deployment

Build command:

```bash
pip install -r backend/requirements.txt
```

Start command:

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Health/root check:

```bash
curl https://sustainable-catalyst-site-intelligence.onrender.com/
```

Expected version:

```json
{"version":"0.8.0"}
```
