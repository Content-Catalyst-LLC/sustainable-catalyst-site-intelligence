# Site Intelligence v4.21.0 — Install and Test

Use the packaged macOS installer with the matching v4.21.0 release bundle. The installer verifies bundle checksums, extracts the immutable repository, creates an isolated Python environment, runs deterministic validation pass 1, reruns immutable/static validation as pass 2, and only then promotes through GitHub/Render.

Do not install the WordPress ZIP until the installer reports that the exact v4.21.0 GitHub/Render live gate passed.

The release gate includes the soils/land overview, four-source catalog, bounded SoilGrids state, readiness contract and browser asset in addition to inherited v4 gates.
