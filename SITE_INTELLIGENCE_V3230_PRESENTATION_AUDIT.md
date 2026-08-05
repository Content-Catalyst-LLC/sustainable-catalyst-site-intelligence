# Site Intelligence v3.23.0 Presentation Audit

## Production problem addressed

The v3.22.9 screenshot showed an improved map renderer inside an application that still behaved like a very long web page. The active map occupied only part of the useful viewport, the evidence column was underused, and many unrelated workspaces remained stacked below the current view.

## Implemented repair

### Bounded application shell

The desktop application now uses a fixed top bar, a scrollable product navigation rail, and a bounded workspace region. The browser page itself no longer expands to the cumulative height of every module.

### Active-route isolation

The global hidden contract is restored with `[hidden]{display:none!important}`. The presentation runtime tracks the active navigation route, hides the overview layout outside the overview route, and invalidates only visible maps after route changes.

### Map-first overview

The primary map and its presentation health strip occupy the main column. Existing metric and context panels are moved into a collapsible evidence drawer. The drawer is persistent on wide screens and becomes an accessible overlay on compact screens.

### Subject-aware framing

Country selection resolves public catalog coordinates and moves the primary map to regional context. The application-level country loader also requests the public country overview and reframes the map when the overview route is active.

### Visible-map health

The presentation check requires:

- a visible managed map;
- at least 300×300 rendered dimensions;
- visible local geography or live map tiles;
- at least two map controls.

The browser publishes `scsi:visible-map-health` and records `data-scsi-presentation-health` on the active map.

### Host-page isolation

The WordPress plugin packages the current map and workspace assets but does not enqueue full-app workspace CSS or JavaScript into the WordPress host page. The standalone application remains isolated inside its iframe.

## Chromium result

The deterministic Chromium harness rendered:

- a 1042×690 primary map;
- 289 local geographic paths;
- 20 live test tiles;
- three map controls;
- Kenya at approximately 0.02°N, 37.91°E and zoom 5;
- a working evidence drawer;
- an isolated non-overview route;
- presentation health `ready`;
- 6,492 distinct screenshot colors;
- 44.76% near-black pixels;
- no console or page errors.
