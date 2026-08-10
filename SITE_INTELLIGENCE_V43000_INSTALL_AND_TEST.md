# Site Intelligence v4.30.0 — Install and Test

1. Place the v4.30.0 release bundle and macOS installer in `~/Downloads`.
2. Run the installer.
3. The installer verifies bundle checksums, creates an isolated Python environment, runs deterministic pass 1, then pass 2 against the unchanged manifest.
4. The promotion script synchronizes GitHub and verifies Render with bounded visible polling and an Industrial deep gate.
5. Install the WordPress plugin only after the exact v4.30.0 Render release gate reports ready.

The installer supports `SC_VERIFY_BUNDLE_ONLY=1` to validate the handoff bundle without promoting production.
