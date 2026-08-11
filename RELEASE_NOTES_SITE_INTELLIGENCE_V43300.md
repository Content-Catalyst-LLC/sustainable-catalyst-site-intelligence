# Site Intelligence v4.34.0 — Global Solid Waste, Recycling & Circular-Materials Intelligence

## Release purpose

v4.34.0 extends the existing Earth/infrastructure continuum into solid-waste systems, recycling infrastructure, hazardous-waste regulatory context, municipal-waste statistics, treatment/recovery/disposal series, and circular-material screening evidence. It is additive inside the existing Earth route and does not change the six primary areas or 35 public navigation routes.

## Registered evidence families

1. **OpenStreetMap Waste & Recycling Infrastructure** — community-mapped landfill, recycling, transfer and disposal features through OpenStreetMap/Overpass.
2. **EPA RCRAInfo / ECHO Hazardous-Waste Records** — U.S. RCRA hazardous-waste handler, treatment/storage/disposal, generator and compliance/enforcement context.
3. **World Bank What a Waste Global Database** — global country/city waste generation, composition, collection and treatment/disposal statistics, including source-identified estimates/projections where applicable.
4. **Eurostat Waste Statistics** — European municipal-waste generation, recycling, recovery, treatment and disposal statistical series through Eurostat web services.

## Governing truth boundary

**SOLID-WASTE & CIRCULAR-MATERIAL EVIDENCE · NOT FACILITY OPERATION, COMPLIANCE, RECYCLING-OUTCOME OR CIRCULARITY DETERMINATION**

The release does not infer that a mapped facility is operating or permitted; does not convert EPA regulatory records into new compliance or health findings; does not convert municipal/national statistics into household or facility outcomes; does not treat reported recycling rates as proof of product/material circularity; and does not treat projected values as observations.

## New public contracts

- `GET /public/solid-waste-circular-materials`
- `GET /public/solid-waste-circular-materials/catalog`
- `GET /public/solid-waste-circular-materials/state`
- `POST /public/solid-waste-circular-materials/feature/normalize`
- `POST /public/solid-waste-circular-materials/regulatory/normalize`
- `POST /public/solid-waste-circular-materials/series/normalize`
- `POST /public/solid-waste-circular-materials/threshold/preview`
- `GET /public/solid-waste-circular-materials/export-manifest`
- `GET /public/solid-waste-circular-materials/readiness`

## Browser integration

The Water & Sanitation environment now deferred-loads `solid-waste-circular-v43300.js`. The new environment uses a mirrored backend/WordPress asset pair and remains inside the existing Earth Observation architecture.

## Deployment safeguards

The v4.33 promoter preserves bounded Render polling, connect/max request timeouts, resume-safe GitHub promotion, rollback tagging, exact version/commit/release-id release-gate verification, and the inherited `backend/backend/` immutable-runtime exclusion. It adds a dedicated Solid Waste deep gate that must verify the overview, four-source catalog, bounded empty state, readiness contract, and `SCSISolidWasteCircularV43300` browser asset before WordPress installation is allowed.
