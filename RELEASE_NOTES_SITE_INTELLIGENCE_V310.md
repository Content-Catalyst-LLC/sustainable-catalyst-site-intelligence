# Site Intelligence v3.1.0 — Live Intelligence Signal Layer

This release adds the Sustainable Catalyst Live Intelligence electronic ticker board. It can be automatically placed immediately below the Astra navigation or inserted manually with `[sc_live_intelligence]`.

## Default behavior

- Black electronic-board background with green dot-matrix-style text.
- Automatic top placement enabled on the homepage only.
- Manual shortcode remains available on any page.
- Automatic placement can be independently turned off.
- Source and freshness labels are shown.
- Hover, keyboard focus, a pause button, and reduced-motion preferences stop movement.
- WordPress proxies and caches the backend feed; API keys never reach the browser.

## Shortcode

```text
[sc_live_intelligence]
[sc_live_intelligence category="platform" limit="6"]
[sc_live_intelligence motion="off"]
```
