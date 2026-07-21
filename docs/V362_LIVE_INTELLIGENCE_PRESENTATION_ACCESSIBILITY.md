# Live Intelligence Presentation and Accessibility — v3.6.2

## Product standard

Motion is optional. Every validated signal remains available through a moving ticker, a fully static strip, or a manual previous-and-next viewer. Presentation choices do not change ranking, freshness, source lineage, or evidence destinations.

## Presentation modes

- **Ticker:** slow, configurable movement with pause on hover, keyboard focus, and a visible pause control.
- **Static:** one non-animated signal strip with bounded horizontal overflow inside the component rather than the page.
- **Manual:** one signal at a time with previous, next, Home, End, arrow-key, and swipe navigation.
- **Mobile stacked:** selected signals appear as static, readable cards.

The public surface displays no more than the configured maximum of one to twelve signals. The recommended default is eight.

## Reduced motion

A visitor's `prefers-reduced-motion` setting overrides moving presentation. Administrators may select either the static strip or manual viewer as the reduced-motion result. Automatic rotation and pulse effects stop, but source links, context pages, and evidence remain available.

## Screen-reader announcements

The animated viewport and delivery badge use `aria-live="off"`. A separate status region announces only the configured events:

- Manual mode announces navigation and pause or resume actions.
- Status mode also announces meaningful delivery-state changes.
- Off mode produces no dynamic announcements.
- Automatic rotation never announces every signal change.

Every signal link retains a complete accessible name containing its category, label, full value, source when enabled, freshness label, and update time. Visual shortening never truncates the accessible name.

## Input and zoom

Previous and next controls have a minimum 44 CSS-pixel target. Manual and rotator modes support arrow keys, Home, End, buttons, and swipe gestures. At narrower layouts and 200% zoom, manual controls move below the signal rather than forcing page-level horizontal overflow.

## No-JavaScript and forced-colors behavior

Without JavaScript, the component exposes a plain explanation and a public feed-status link. Forced-colors mode removes glow-dependent communication and uses system colors and visible control borders.

## Boundaries

- Live Intelligence is not an emergency-warning service.
- Motion is never required to understand or open a signal.
- Accessibility settings do not personalize source ranking.
- The browser receives no upstream API credentials.
- Astra navigation and breadcrumb styles remain untouched.
