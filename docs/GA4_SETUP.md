# GA4 Setup for Sustainable Catalyst Site Intelligence

This package uses GA4 as the primary analytics data source and Sustainable Catalyst metadata as the interpretation layer.

## 1. Enable the Google Analytics Data API

In Google Cloud Console:

1. Create or select a Google Cloud project.
2. Enable the Google Analytics Data API.
3. Create a service account.
4. Create a JSON key for that service account.
5. In Google Analytics Admin, add the service account email to the GA4 property with Viewer access.

## 2. Add Render environment variables

Set these in the Render web service:

```text
SC_SI_ENVIRONMENT=production
SC_SI_DEMO_MODE=false
SC_SI_CORS_ORIGINS=https://sustainablecatalyst.com
SC_SI_API_TOKEN=replace-with-long-random-token
SC_SI_GA4_PROPERTY_ID=your-property-id
SC_SI_GOOGLE_APPLICATION_CREDENTIALS_JSON={...full service account json...}
```

Do not commit the service account JSON file to GitHub.

## 3. Recommended GA4 custom dimensions

Create event-scoped custom dimensions for:

```text
sc_content_hub
sc_article_map
sc_content_type
sc_discipline
sc_pathway_id
sc_tool_id
sc_repository_present
sc_repository_url
```

These dimensions make GA4 reports readable through the Sustainable Catalyst knowledge model.

## 4. Recommended custom events

The WordPress bridge emits:

```text
sc_repository_click
sc_workbench_open
sc_research_librarian_open
sc_decision_studio_open
sc_pathway_continue
sc_library_nav
sc_scroll_depth
```

These should appear in GA4 if your GTM/GA4 configuration forwards `dataLayer` events or if you add equivalent GTM triggers.

## 5. How the backend queries GA4

The backend currently calls two reports:

Page report:

```text
dimensions: pagePath, pageTitle
metrics: screenPageViews, activeUsers, eventCount, engagementRate, averageSessionDuration
```

Event report:

```text
dimensions: pagePath, eventName
metrics: eventCount
```

## 6. Important limitation

GA4 is the source of record for v0.1.0. The `/collect/event` endpoint accepts event payloads but does not store them yet. That endpoint is included so future builds can add a first-party event store, BigQuery export sync, or Measurement Protocol forwarding.
