# Site Intelligence v4.38.0 — Live Space & Iframe Audit

## Scope

This audit certifies the five-lane live Space control plane and the WordPress iframe navigation repair.

## Space truth boundaries

- Archive discovery is not a live telescope feed.
- Planetary STAC assets remain tied to source processing level and product fitness-for-use limits.
- JPL Horizons values are authoritative only for the submitted body/observer/epoch request; local orientation drawings are not ephemerides.
- NASA Exoplanet Archive parameters do not establish habitability, biosignatures, surface conditions, or life.
- SETI archive records, candidate/event labels, and search products are not confirmation of extraterrestrial intelligence.
- Empty or degraded provider responses remain empty/degraded; Site Intelligence does not fabricate replacement observations.

## Provider architecture

| Lane | Source family | Credential required for core lane | Release blocking |
|---|---|---:|---:|
| Planetary imagery | USGS Astrogeology STAC | No | No |
| Astronomy observations | MAST / STScI | No | No |
| Solar-system ephemeris | NASA JPL Horizons | No | No |
| Exoplanets | NASA Exoplanet Archive TAP | No | No |
| SETI archive | Breakthrough Listen | No | No |

Readiness is network-free. Live searches occur only when a user requests a provider query.

## Iframe repair

Dedicated browser certification covers iframe widths 1024px, 900px, and 768px. At each width the navigation rail is 236px, Ocean/Space labels remain visible, and text does not overflow horizontally. The <=760px mobile navigation contract is preserved.

## Browser certification

- Live Space panel visible: PASS
- Default provider: `astronomy-observations`: PASS
- Source-attributed candidate records: PASS
- Six Space module handoffs: PASS
- 1024/900/768 iframe text controls: PASS
- Ocean standalone 11 systems / 5 groups: PASS
- Desktop 35/35 routes: PASS
- Mobile 35/35 routes: PASS
- Iframe 35/35 routes: PASS
- Palestine/Israel identity integrity: PASS
- Country evidence presentation: PASS
