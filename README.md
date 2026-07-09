# Sustainable Catalyst Site Intelligence

**Version:** 0.8.1  
**Build:** Public Dashboard Brief Gateway Patch

Site Intelligence is a FastAPI + WordPress plugin system for Sustainable Catalyst analytics, registry coverage, search intelligence, external source dashboards, public dashboard summaries, reports, exports, and AI-assisted internal briefs.

## v0.8.1 patch

v0.8.1 patches the AI Public Dashboard Brief so public-page rendering remains stable:

- `[sc_ai_public_dashboard_brief]` now relies on a fast public-safe snapshot.
- The source report avoids live analytics-backed public dashboard generation during shortcode render.
- WordPress proxy errors suppress raw HTML/Cloudflare gateway pages.
- Frontend JavaScript sanitizes unexpected HTML errors before displaying them.

## Deployment

Render build command:

```bash
pip install -r backend/requirements.txt
```

Render start command:

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Health/version check:

```bash
curl "https://sustainable-catalyst-site-intelligence.onrender.com/"
```

Expected version:

```json
{"version":"0.8.1"}
```

## AI brief shortcodes

```text
[sc_ai_brief_status]
[sc_ai_site_intelligence_brief]
[sc_ai_search_brief]
[sc_ai_publishing_brief]
[sc_ai_external_sources_brief]
[sc_ai_public_dashboard_brief]
```

AI remains disabled by default unless provider environment variables are configured.
