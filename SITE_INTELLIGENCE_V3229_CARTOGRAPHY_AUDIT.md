# Site Intelligence v3.22.9 Cartography Audit

## Production presentation problem

v3.22.8 restored dependable geographic rendering, but the result remained visually weak. The primary map could appear almost black, satellite imagery could dominate or obscure geographic context, the local fallback lacked a strong label hierarchy, and some map panels looked empty even though the browser considered them initialized.

## Root causes

### Flat fallback geography

The local Natural Earth geometry provided resilience but was rendered with nearly uniform styling. Country identity, label priority, regional differentiation, and scale context were not encoded strongly enough for an intelligence workspace.

### Undifferentiated raster layers

Base-map and imagery tiles shared one presentation path. The engine did not expose distinct base, imagery, and overlay roles with predictable stacking, so satellite imagery could visually replace rather than complement geographic context.

### Decorative masks over the map

The orbital glow and vignette treatment produced an oversized dark circular form over the primary map. This made a functioning map appear blank or broken.

### Inadequate browser-visible quality checks

Previous checks proved that paths, assets, and controls existed. They did not measure whether the rendered result contained enough color variation, avoided an overwhelmingly black surface, or retained readable labels and scale context.

## v3.22.9 repairs

### Shared vector-cartography engine

`vector-cartography-v3229.js` remains self-hosted and loads before all application modules. It preserves the existing Leaflet-compatible integration surface used across Site Intelligence while adding explicit raster roles, local vector geography, country labels, scale, coordinates, and rendered-quality metadata.

### Enriched local geography

`world-cartography-v3229.geojson` contains 177 Natural Earth country features. Each feature includes:

- country name and ISO identity;
- label latitude and longitude;
- zoom-aware label rank;
- geographic extent score;
- cartography class for restrained regional differentiation.

The geography is packaged in both the FastAPI public application and the WordPress plugin, and is available before optional remote tiles.

### Stable layer order

The renderer uses a fixed visual order:

1. deep-slate map background;
2. base raster tiles when available;
3. local country and coastline geography;
4. satellite or thematic imagery with controlled opacity;
5. evidence polygons and lines;
6. event markers, labels, popups, and controls.

A failed imagery layer therefore cannot erase the base map or local boundaries.

### Cartographic hierarchy

The CSS defines differentiated but restrained land fills, national borders, water context, label ranks, evidence strokes, raster filters, scale, coordinate readout, and quality status. Red remains reserved for active evidence and interface emphasis rather than becoming a general map fill.

### Map sizing and mask removal

The main map uses a controlled `clamp(520px, 62vh, 720px)` height on desktop with responsive behavior below it. The orbital glow and vignette masks are disabled so they cannot cover the map surface.

## Chromium evidence

The deterministic Chromium harness creates two independent map surfaces using the exact shipped JavaScript, CSS, and local geography. It supplies controlled base and satellite tiles without relying on the public internet and verifies:

- two map instances initialize in `vector-cartography-engine` mode;
- more than 150 local boundary paths render on each surface;
- zoom-aware country labels render;
- base and imagery tiles occupy separate panes with imagery above the base;
- evidence geometry and markers remain visible;
- map controls, scale, and coordinate readout render;
- both containers have non-zero dimensions;
- the rendered map contains more than 100 distinct colors;
- the near-black pixel ratio remains below the failure threshold;
- no Chromium console or page errors occur.

The final observed smoke result rendered 289 boundary paths per map, 7,335 distinct colors, and approximately 5.2% near-black pixels.

## Known boundary

This release improves the packaged cartographic engine and presentation without bundling a planet-scale street-level vector tile archive. OpenStreetMap, CARTO, and NASA raster sources remain optional network layers. The bundled local geography guarantees country-scale context, labels, and evidence overlays when those providers are unavailable.
