# Site Intelligence v4.33.0 Audit — Solid Waste, Recycling & Circular Materials

## Scope

This audit documents the evidence boundaries and release controls for Global Solid Waste, Recycling & Circular-Materials Intelligence.

## Source registry

### OpenStreetMap Waste & Recycling Infrastructure
- Public documentation: `https://wiki.openstreetmap.org/wiki/Tag:amenity%3Drecycling`
- Landfill context: `https://wiki.openstreetmap.org/wiki/Tag:landuse%3Dlandfill`
- Query surface: Overpass API.
- Evidence role: community-mapped recycling/disposal/landfill/transfer geometry and attributes.
- Guard: mapped geometry is not proof of current operation, permission, accepted materials, capacity or compliance.

### EPA RCRAInfo / ECHO Hazardous-Waste Records
- Public web services: `https://echo.epa.gov/tools/web-services`
- Data/download context: `https://echo.epa.gov/tools/data-downloads/rcrainfo-download-summary`
- Evidence role: U.S. hazardous-waste handler and regulatory/compliance context.
- Guard: source records are administrative/regulatory evidence and are not live facility inventory, exposure telemetry, a new violation finding, remediation order or legal determination by Sustainable Catalyst.

### World Bank What a Waste Global Database
- Catalog: `https://datacatalog.worldbank.org/search/dataset/0039597/what-a-waste-global-database`
- Metadata observed during v4.33 source review: database refreshed in March 2026; 217 countries and 262 cities; CC BY 4.0; source metadata identifies estimates and projections.
- Evidence role: generation, composition, collection, treatment/disposal and related waste-system statistics.
- Guard: aggregated statistics do not establish specific household collection, facility performance, actual material recovery or local compliance.

### Eurostat Waste Statistics
- Waste data information: `https://ec.europa.eu/eurostat/web/waste/information-data`
- API guidance: `https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction`
- Municipal waste dataset: `env_wasmun`.
- Evidence role: official European waste-generation, treatment, recovery, disposal and recycling series.
- Guard: national/statistical recycling values are not product/material circularity certification, facility performance or waste-shipment trace evidence.

## Explicit false/non-inference guards

- `mapped_waste_feature_equals_operating_facility = false`
- `regulatory_record_equals_new_compliance_finding = false`
- `waste_statistic_equals_facility_or_household_outcome = false`
- `reported_recycling_rate_equals_material_circularity = false`
- `projection_equals_observed_future_waste = false`
- `zero_records_equals_no_waste_infrastructure = false`
- `automatic_action_authorized = false`

## Architecture

- Primary public areas: unchanged.
- Public navigation routes: unchanged at 35.
- New domain is deferred inside Earth Observation.
- Backend and WordPress assets are mirrored exactly.
- Service worker includes v4.33 JS/CSS.
- No automatic enforcement, public-health, procurement, investment, remediation or operational action is authorized.
