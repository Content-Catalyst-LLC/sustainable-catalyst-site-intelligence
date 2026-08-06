# Site Intelligence v3.23.6.2 Mutation Observer Audit

## Failure reproduced

The v3.23.5 browser-reliability module observed the active workspace and unconditionally assigned `summary.textContent` in its callback. Each assignment generated another child-list mutation, producing an unbounded callback/write cycle. The browser stopped before Data Truth and Production Truth initialized.

## Recovery contract

1. Summary text is computed before writing and assigned only when changed.
2. Mutation callbacks schedule one animation-frame task rather than writing immediately.
3. The workspace observer is disconnected while generated summaries and `aria-describedby` values are updated.
4. Summary-node mutations are ignored.
5. Summary work is capped at eight passes per second and suppression is exposed in runtime state.
6. The complete-shell browser gate requires the final application state, Data Truth, Production Truth, visible map dimensions, bounded observer activity, and zero page errors.

## Gate behavior

The release verifier searches common macOS and command-line Chrome, Chromium, Edge, and Brave paths. Missing browser or Playwright support is a release-blocking error.
