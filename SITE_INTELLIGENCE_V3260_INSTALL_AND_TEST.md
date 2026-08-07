# Site Intelligence v3.26.0 Install and Test

1. Put the v3.26.0 release bundle and installer in `~/Downloads`.
2. Run the installer. It verifies checksums, creates an isolated Python environment, runs two deterministic validation passes, promotes the exact Git tree, waits for Render, and verifies the live release gate.
3. Install the WordPress ZIP only after the installer reports that the exact v3.26.0 Git commit and live assurance contracts passed.

The live gate verifies the application shell, country selector, Data Truth, Record Provenance, Data Truth Control Plane, Unified Analytical State, Comparative/Scenario/Model Assurance, browser reliability, startup stability, service-worker strategy, production truth, runtime health, and WordPress embed contract.
