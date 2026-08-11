# Site Intelligence v4.34.0 — Install and Test

Use the release bundle and macOS installer together. The installer verifies bundle checksums, extracts the repository, creates an isolated Python environment, runs deterministic validation, promotes through GitHub/Render, waits for the exact release gate, and only then prints the WordPress ZIP path.

Do not install the WordPress plugin before the live backend reports v4.34.0 and the expected Git commit/release ID.

## Local validation contracts

- v4.34 static release contract
- immutable manifest verification
- JavaScript syntax
- JSON / GeoJSON parsing
- WordPress PHP syntax
- static security scan
- complete pytest collection (1,358 tests)
- direct / iframe-compatible SETI browser gate

The SETI panel is intentionally lazy-loaded from the Astronomical Observation Environment to preserve the inherited application-shell performance budget.
