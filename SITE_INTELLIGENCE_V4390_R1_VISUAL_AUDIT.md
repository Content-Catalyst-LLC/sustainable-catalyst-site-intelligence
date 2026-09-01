# Site Intelligence v4.39.0 R1 — Visual Audit

## Capability communication

- Earth, Space, and Ocean are shown with authentic scientific imagery rather than generic stock photography.
- Geographic, Earth systems, Ocean, and Orbital capability labels remain visible in text.
- The orbital overlay is decorative and does not claim that its nodes represent current events or exact coordinates.
- Current operational claims remain confined to backend-provided metrics, status, and signal records.

## Interaction

- The original ticker remains moving by default when the administrator-selected presentation mode is `ticker`.
- The ticker pauses through its existing explicit pause control, keyboard focus behavior, and pointer hover behavior.
- Reduced-motion preferences continue to switch away from forced ticker animation.
- The three images are lazy-loaded and decoded asynchronously.
- Image sources are self-hosted; source pages are linked in the visible credit line.

## Responsive behavior

- Desktop: text and capability imagery form a two-column console.
- Tablet: the visual column narrows while metrics and signals use two columns.
- Mobile: the visual moves below the introduction, the ticker retains its governed mobile behavior, and cards become a single column.
- Very small screens retain a two-column metric grid while hiding secondary image-caption text.

## Accessibility

- Images include specific alternative text.
- Image credits are keyboard-accessible links.
- Decorative orbit paths and nodes are hidden from assistive technology.
- Existing `aria-live`, status, no-script, forced-colors, and reduced-motion behavior remains intact.
