# Site Intelligence v1.18.2 — WordPress Skeleton Loader Completion Patch

## Problem

The Country Intelligence Profile and Cross-Domain Comparison shortcodes could render complete results while leaving their three skeleton bars visible.

## Repair

The WordPress frontend now:

1. sets `aria-busy=true` before a request;
2. renders success, fallback, or error content;
3. always runs loading cleanup in `Promise.finally`;
4. sets `aria-busy=false`;
5. hides and removes the loading shell from the DOM.

CSS also guarantees that hidden or completed loading shells cannot be displayed.

## Missing comparison values

Unavailable values remain explicit. The public wording is now:

> No validated public value is currently available.
