# Site Intelligence v3.23.6.3 Browser Reliability Audit

## Objective

Make the v3.23.4 analytical workspace dependable on phones, tablets, current desktop browsers, keyboard-only navigation, reduced-motion environments, forced-color modes, slow connections, and long-running sessions.

## Production contract

The release publishes `/public/browser-reliability`, backed by `browser_reliability_policy_v3235.json`. The contract declares supported browser families, viewport profiles, accessibility controls, recovery behaviors, and explicit claim boundaries.

## Browser implementation

`browser-reliability-v3235.js` runs only when the document contains the matching Site Intelligence application root. It does not execute diagnostics in the surrounding WordPress host document.

The runtime:

- Classifies phone, tablet, and desktop viewports.
- Detects coarse pointers, reduced motion, Save-Data, and slow connections.
- Restores focus to the active workspace heading after routed navigation.
- Contains keyboard focus within open dialogs and the evidence drawer.
- Restores focus to the control that opened a modal surface.
- Generates screen-reader map summaries from visible rendered content.
- Recovers map layout after bounded resize, orientation, visibility, and inactivity events.
- Exposes a low-bandwidth control and a browser heartbeat event.

## Styling implementation

`browser-reliability-v3235.css` adds 44-pixel touch targets, responsive topbar and evidence-drawer behavior, visible keyboard focus, reduced-motion rules, forced-color support, safe-area spacing, and low-bandwidth imagery suppression.

## Validation boundaries

Automated validation confirms contract structure, asset packaging, service-worker inclusion, runtime-health coverage, host isolation, mobile viewport behavior, focus restoration, map summaries, and low-bandwidth state. It does not constitute a formal WCAG conformance audit or testing on physical devices.
