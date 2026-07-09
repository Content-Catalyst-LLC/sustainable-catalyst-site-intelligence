# Public API Source Expansion — v1.2.0

Site Intelligence v1.2.0 adds the first public API source expansion layer. The goal is to make Site Intelligence stronger as a public intelligence system without exposing private analytics, credentials, raw API payloads, or unreleased operational details.

## Public endpoints

- `/public/sources`
- `/public/sources/health`
- `/public/sources/development-indicators`
- `/public/sources/research-metadata`
- `/public/sources/publications`
- `/public/sources/repositories`
- `/public/indicators/overview`
- `/public/indicators/sustainability`

## Public shortcodes

- `[sc_public_api_sources]`
- `[sc_public_source_health]`
- `[sc_public_development_indicators]`
- `[sc_public_research_metadata]`
- `[sc_public_publication_metadata]`
- `[sc_public_repository_intelligence]`
- `[sc_public_indicator_overview]`
- `[sc_public_sustainability_indicators]`

## Source families

The public source layer groups APIs and metadata systems into public-safe source families:

- Climate + Energy: NASA POWER, NASA GIBS, Climate TRACE, NOAA/NWS, EIA
- Environmental Monitoring: EPA AQS, USGS, NOAA/NWS, NASA GIBS
- Biodiversity + Land Use: GBIF, USGS, NASA GIBS
- Development Indicators: World Bank, OECD, UN/SDG data
- Research Metadata: OpenAlex, Crossref
- Repository Intelligence: GitHub repositories, release metadata, documentation coverage

## Public-safe behavior

The source layer uses live/cached/fallback/planned labels so public pages can explain what is shown without overstating source availability. Public output should show source context, status labels, methodology notes, and interpretation boundaries.

## Excluded from public display

- API keys and credentials
- Raw upstream API payloads
- Force-refresh diagnostics
- Backend logs
- Private analytics and query data
- Unreleased reports and AI briefs
- Professional assurance or certification claims

## Next build direction

v1.2.0 prepares the platform for deeper live integrations. Future builds can add live adapters for World Bank, OpenAlex, Crossref, GitHub, OECD, and UN/SDG data while keeping cached and fallback-safe public displays.
