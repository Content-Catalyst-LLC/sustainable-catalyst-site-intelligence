# Site Intelligence v3.23.0

## Cartographic Workspace and Application Presentation

This release rebuilds Site Intelligence as a bounded, route-driven intelligence application rather than a single continuously stacked page.

### Application presentation

- Introduces a stable map-first overview workspace.
- Places signals, country context, and evidence coverage in a collapsible evidence drawer.
- Ensures only the active routed workspace contributes to document flow.
- Removes the oversized orbital mask, vignette, and decorative blue page field.
- Uses a restrained black, charcoal, slate, white, and red institutional interface.
- Keeps the primary map between 520 and 720 pixels high on desktop.
- Gives every secondary map a stable pre-initialization height.
- Adds responsive sidebar, drawer, and mobile navigation behavior.

### Cartographic behavior

- Automatically reframes the overview map to the selected country.
- Preserves local Natural Earth geography when network tiles are unavailable.
- Reduces label collisions and prevents imagery from wrapping horizontally around the world.
- Preserves evidence overlays, keyboard navigation, drag, zoom, scale, coordinates, and reset controls.

### Browser-visible health

The active map is presentation-ready only when it has usable dimensions, visible geography or tiles, and working controls. Hidden workspaces no longer affect the visible health result.

### WordPress boundary

The full application workspace CSS and JavaScript remain inside the Render iframe. They are packaged in the WordPress release for parity but are not enqueued into the host WordPress document, preventing global body, overflow, and navigation styles from contaminating the site theme.
