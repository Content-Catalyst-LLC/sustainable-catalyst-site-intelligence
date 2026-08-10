# Site Intelligence v4.22.0 — Install and Test

1. Place the v4.22.0 installer and release bundle in `~/Downloads`.
2. Run the installer.
3. The installer verifies bundle checksums, extracts the repository, creates an isolated Python environment, runs deterministic validation pass 1, runs pass 2 against the unchanged package, promotes GitHub refs, and verifies Render.
4. The Render verifier prints each poll rather than appearing silent.
5. Install the WordPress ZIP only after the terminal reports that the exact v4.22.0 live release gate passed.

The installer may be rerun safely to resume Render verification if GitHub already contains the release commit/tag.
