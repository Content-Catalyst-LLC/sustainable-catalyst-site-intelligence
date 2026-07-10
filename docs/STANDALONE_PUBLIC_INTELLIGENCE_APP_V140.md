# Site Intelligence v1.14.0

## Standalone Public Intelligence App and Visual System

v1.14.0 replaces the shortcode-stacked public experience with a dedicated map-first application served by the FastAPI backend at `/app/`.

### Public routes

- `/app/` — overview workspace
- application navigation: Overview, Country, Events, Compare, Sources
- `/public/geospatial/*` — satellite, event, heat-map, timeline, and accessibility data
- `/public/country-intelligence/{ISO3}` — country evidence structure

### WordPress embedding

Use:

`[sc_site_intelligence_app height="900"]`

WordPress supplies the host page. The standalone application owns the visual workspace.

### Design boundaries

- backend status and connector diagnostics are not promoted as primary public content
- missing values remain explicit
- satellite imagery dates and provenance remain visible
- event records are not operational alerts
- density does not imply severity or causality
