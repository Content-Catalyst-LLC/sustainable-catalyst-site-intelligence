# Offline, Mobile, Accessibility, and Performance — v2.12.0

Site Intelligence v2.12.0 adds a browser-managed application shell and public engineering diagnostics without changing the evidentiary meaning of any data.

## Delivery model

- Navigation uses a network-first strategy with an explicit offline page.
- First-party application assets use stale-while-revalidate caching.
- Public JSON uses network-first delivery with a bounded cached fallback.
- Writes remain network-only.
- External map tiles and imagery are not promised offline.

## Privacy and control

Offline preferences and cached responses remain in browser storage. Users can clear the Site Intelligence cache from the experience workspace or through browser settings. No account or hosted profile is created.

## Accessibility boundary

The release targets WCAG 2.2 Level AA and exposes automated contracts for keyboard access, focus, reduced motion, forced colors, touch targets, and text alternatives. This is not third-party certification; screen-reader, zoom, real-device, and representative network testing remain required.
