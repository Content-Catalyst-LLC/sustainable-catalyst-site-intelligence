# Site Intelligence v3.23.7.2 — Country Dropdown Interaction and Focus Safety

## Purpose

This patch repairs the global country selector after v3.23.7.1 successfully populated the catalog but background workspace-state checks repeatedly moved focus back to the route heading. In a native browser selector that focus change closes the option menu before a user can scroll.

## Repairs

- Preserve focus while a user is interacting with `select`, `input`, `textarea`, combobox, listbox, or editable controls.
- Deduplicate route-heading focus so repeated ready/degraded state evaluations do not refocus the same route.
- Keep route-focus accessibility behavior for genuine route transitions.
- Restore browser-managed touch, trackpad, mouse-wheel, and keyboard behavior on the global country selector.
- Keep all country options and the v3.23.7 Global Country Data Truth contracts unchanged.
- Add direct-shell and WordPress-iframe browser gates covering focus retention, unblocked wheel interaction, first/last catalog selection, Brazil selection, and Data Truth synchronization.

## Validation repair

The first package used Home/End key assertions that are not portable for a closed native `<select>` in headless Chrome on macOS. The failed result showed that focus remained on the selector and Brazil updated Data Truth correctly. The repaired gate now tests the cross-platform interaction contract without relying on operating-system popup behavior.

## Boundaries

This patch does not fabricate country data, broaden source coverage, or alter Data Truth classifications. It repairs selection interaction only.
