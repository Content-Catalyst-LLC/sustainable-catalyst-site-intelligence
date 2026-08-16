# Site Intelligence v4.38.0 — Live Space Observation, Planetary Imagery & Archive Retrieval + Iframe Navigation Repair

## Release purpose

v4.38.0 turns the featured Space pillar from a mostly source-aware handoff layer into a live, provider-bounded observation/archive workspace while repairing the text-control collision seen in WordPress iframe widths. It preserves the existing six primary areas and 35 canonical public routes.

## Live Space acquisition lanes

1. **Planetary imagery** — USGS Astrogeology STAC discovery for Moon/Mars collections and source-attributed assets.
2. **Astronomical observations** — MAST/STScI observation discovery by target or sky coordinate.
3. **Solar-system ephemerides** — authoritative JPL Horizons responses for body, observer, and epoch requests.
4. **Exoplanets** — NASA Exoplanet Archive TAP records with parameter/reference semantics retained.
5. **SETI archive discovery** — Breakthrough Listen public archive metadata/handoffs without promoting candidates into confirmation claims.

All five core lanes are credential-free from the Site Intelligence release perspective. Provider/upstream failure is non-blocking and does not cause local fabrication or silent substitution.

## Space interface

The Science workspace now includes a first-class Live Space surface with provider selection, target/body, RA/Dec/radius, epoch controls, bounded search results, source-record URLs, provenance/metadata detail, and direct handoffs to Orbital Earth, Planetary, Astronomy, Solar System, Exoplanets, and SETI. MAST astronomical observations are the default lane.

## Iframe navigation repair

The legacy <=1050px rule compressed the sidebar to 80px while newer featured Ocean/Space controls forced their labels visible. v4.38.0 introduces an embed-aware 761–1180px layout with a 236px text sidebar, controlled wrapping, and no horizontal label overflow. At <=760px the existing mobile navigation model remains authoritative.

## Inherited guarantees

- Ocean remains a first-class featured system with 11/11 marine systems.
- Live Underwater media discovery from v4.37.0 remains intact.
- Platform Core remains optional for local Ocean/Space discovery.
- Palestine/Israel canonical identity isolation remains intact.
- Country operational evidence remains separated from structural/harmonized indicators.
- Six primary areas / 35 canonical routes remain unchanged.

## Release identity

- Semantic version: `4.38.0`
- Git tag: `v4.38.0`
- Rollback tag: `site-intelligence-pre-v4.38.0`
- Expected deterministic pytest collection: `1708`
