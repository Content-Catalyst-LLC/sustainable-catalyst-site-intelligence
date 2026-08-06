# Site Intelligence v3.23.6.3

## Mutation Observer Recovery and Complete-Shell Browser Gate

This emergency release repairs the browser freeze inherited from v3.23.5 through v3.23.6.1. The browser-reliability runtime previously rewrote map-summary text from inside an observer watching the same workspace, creating a self-triggering mutation cycle.

### Repairs

- Writes map summaries only when the computed text changes.
- Schedules summary work through one animation frame.
- Disconnects the observer while summaries and accessibility relationships are written.
- Ignores mutations originating inside generated summary nodes.
- Limits map-summary processing to eight passes per second.
- Preserves single-owner service-worker startup and fail-open loading recovery.
- Adds a mandatory complete-shell Chromium gate that loads the exact production script chain.
- Validation now fails when Chrome/Chromium or Playwright is unavailable instead of recording the browser gate as skipped.

### Production boundary

The installer verifies repository and API contracts locally, then requires a real browser execution of the complete application shell before promotion. Live GitHub, Render, and WordPress deployment remain actions performed by the macOS installer.
