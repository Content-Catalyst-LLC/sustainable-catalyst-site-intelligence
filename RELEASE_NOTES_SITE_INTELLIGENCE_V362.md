# Site Intelligence v3.6.2 — Live Intelligence Presentation, Motion, and Accessibility Controls

Site Intelligence v3.6.2 completes the presentation and accessibility increment of the Live Intelligence homepage surface while preserving the v3.6.1 reliability boundary.

## Included

- Administrator-selectable slow ticker, fully static strip, and manual signal viewer.
- Reduced-motion override to static or manual presentation.
- Mobile stacked-card mode in addition to rotator, marquee, and hidden modes.
- Previous, next, Arrow Left, Arrow Right, Home, End, and swipe navigation.
- Minimum 44 CSS-pixel navigation targets.
- Configurable maximum of one to twelve visible signals, defaulting to eight.
- Animated viewport and delivery badge removed from live-region announcements.
- Dedicated, bounded assistive announcer for manual actions and optional delivery-state changes.
- Complete accessible signal names even when visual text is shortened.
- No-JavaScript public feed-status fallback.
- Forced-colors and 200% zoom behavior.
- Public `/public/live-intelligence/presentation-policy` endpoint and WordPress proxy route.
- 642-test regression coverage.

## Preserved

Signal validation, freshness states, same-query last-known-good recovery, honest empty geographic results, source operations, topic and regional channels, clustering, ranking, context pages, evidence records, source attribution, WordPress cache controls, Astra navigation, and breadcrumb styling remain intact.

## Boundaries

Motion is never required to understand or open a signal. Automatic rotation does not announce every item to screen readers. Presentation choices do not alter source selection, ranking, freshness, or evidence lineage. Live Intelligence remains an informational research surface rather than an emergency-warning service.
