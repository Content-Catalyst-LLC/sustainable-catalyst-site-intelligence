# Site Intelligence v4.21.0 — Global Soils, Land Degradation & Desertification Intelligence

## Purpose

Extend Earth Observation from solid-Earth and terrestrial-system context into soil properties, soil survey evidence, soil moisture and land-degradation reporting without adding a new top-level route family.

## Source registry

1. **ISRIC SoilGrids** — global predictive soil-property maps and REST access. The REST v2 service remains beta and publishes a fair-use policy; model predictions remain distinct from direct soil samples.
2. **USDA-NRCS Soil Data Access** — official U.S. and Island Jurisdiction soil-survey spatial/tabular data through REST, WFS and WMS services.
3. **NASA SMAP / NSIDC DAAC** — satellite soil-moisture retrievals and model-assimilated surface/root-zone products; processing level is retained.
4. **UNCCD SDG 15.3.1 / Land Degradation Neutrality reporting** — country-reported indicators and UNCCD default estimates with partial-reporting context preserved.

## Truth boundary

**SOIL & LAND EVIDENCE · NOT A SITE INVESTIGATION, LAND-DEGRADATION DECLARATION OR CARBON CLAIM**

- SoilGrids predictions are not direct ground samples.
- Soil-survey map units are not parcel boundaries or site-specific engineering determinations.
- SMAP L2/L3 retrievals and L4 model-assimilated fields remain distinct evidence classes.
- UNCCD country reports and default estimates are not silently represented as a comprehensive independent global assessment.
- A land-degradation indicator does not by itself establish causal attribution or a Sustainable Catalyst desertification declaration.
- Soil organic carbon values do not become a carbon-credit, sequestration-verification or project-certification claim.
- Empty results do not mean healthy soil or absence of land degradation.

## Public contracts

- `GET /public/soils-land`
- `GET /public/soils-land/catalog`
- `GET /public/soils-land/state`
- `POST /public/soils-land/measurement/normalize`
- `POST /public/soils-land/assessment/normalize`
- `POST /public/soils-land/threshold/preview`
- `GET /public/soils-land/export-manifest`
- `GET /public/soils-land/readiness`

The six-primary-area / 35-public-route architecture is preserved.
