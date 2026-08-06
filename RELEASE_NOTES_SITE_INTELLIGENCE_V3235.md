# Site Intelligence v3.23.7

## Browser Reliability, Mobile, and Accessibility

This release hardens the existing map-first analytical application across supported desktop and mobile browsers without adding a new analytical feature family.

### Delivered

- Capability-based support contract for current Chromium, Safari, Firefox, and Edge.
- Phone, tablet, and desktop viewport profiles.
- Route-change focus management and live-region announcements.
- Keyboard containment and focus restoration for dialogs and the evidence drawer.
- Browser-generated text summaries for visible map surfaces.
- Reduced-motion and forced-color support.
- Minimum 44-pixel touch targets for coarse-pointer devices.
- Low-bandwidth mode with Save-Data and slow-connection detection.
- Optional imagery suppression without changing evidence values.
- Bounded resize, orientation, visibility, and long-session recovery.
- Application-only execution that preserves WordPress host isolation.
- Public browser reliability contract at `/public/browser-reliability`.

### Boundaries

The accessibility contract is not a claim of third-party certification. Map text summaries provide an equivalent orientation layer but do not replace source provenance or analytical interpretation. Low-bandwidth mode changes presentation and network demand only; it does not alter source values.
