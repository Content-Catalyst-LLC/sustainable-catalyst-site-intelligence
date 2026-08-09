# Site Intelligence v4.1.0 Install and Test

Use the release-bundle installer rather than manually copying repository files.

The installer verifies SHA-256 bundle checksums, creates an isolated Python environment, runs the deterministic verifier twice, synchronizes the exact validated Git tree, publishes the release tag, waits for the Render release gate, and verifies the new Monitoring Operations contract before permitting WordPress installation.

The mandatory v4.1.0 browser gates cover Monitoring Operations, Research Integration, comparative/model assurance, country-selector interaction and hydration, complete-shell initialization, production soak, service-worker closure, and fixed WordPress embed isolation.

Install the WordPress ZIP only after the live GitHub/Render gate reports success for the exact v4.1.0 commit and release id.
