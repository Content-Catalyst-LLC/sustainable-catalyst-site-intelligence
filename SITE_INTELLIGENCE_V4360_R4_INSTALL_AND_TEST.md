# Site Intelligence v4.38.0 R4 — Install and Test

Use the R4 release bundle and run `deploy_and_validate_site_intelligence_v4_36_0_R4_macos.sh` on macOS. The installer verifies bundle checksums, creates an isolated Python environment, runs the deterministic test suite, runs browser certification, pushes the certified tree to GitHub, and waits for Render promotion.

After backend promotion, replace the WordPress plugin with the R4 plugin ZIP even though WordPress still reports semantic version `4.38.0`. R4 is release lineage and frontend cache/controller repair.

Expected browser certification:

- featured navigation labels: Ocean, Space
- direct Space entry: six local workspaces
- direct Ocean entry: 11 marine systems, hydration ready
- Production Truth: ready for Ocean-owned Earth route
- desktop/mobile/iframe route gates: 35/35
