# Site Intelligence v3.23.6.4 — Fixed Application Viewport and WordPress Embed Isolation

This patch isolates the complete Site Intelligence application from WordPress document-height negotiation. The standalone application remains full-document in its own tab, while `[sc_site_intelligence_app]` now renders as a fixed-height application viewport with internal scrolling.

## Changes

- Fixed the full application iframe at the shortcode height.
- Disabled child height messages in `embed=wordpress` application mode.
- Ignored document-height messages for fixed application frames in WordPress.
- Removed the inherited eight-pixel height addition and height animation.
- Removed `content-visibility:auto` and containment from the full application wrapper.
- Preserved bounded automatic resizing for smaller document-oriented embeds.
- Corrected the malformed `data-scsi-release` shortcode attribute.
- Added dynamic synchronization for the public page's current-version status and release bar.
- Added `/public/embed-isolation` and a mandatory long-page WordPress browser gate.

## Boundary

Static editorial paragraphs elsewhere on the WordPress page remain page content and are not rewritten by the repository package.
