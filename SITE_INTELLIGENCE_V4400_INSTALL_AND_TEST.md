# Site Intelligence v4.13.0 — Install and Test

Use the release-bundle installer rather than manually copying repository files.

The installer verifies bundle SHA-256 checksums, extracts the exact repository ZIP, creates an isolated Python virtual environment, installs backend and development requirements, runs the deterministic v4.13.0 verifier, performs a fast second deterministic pass, promotes the exact validated source through GitHub/Render, and waits for the live release gate.

The WordPress ZIP should be installed only after the installer reports that the exact v4.13.0 GitHub/Render live gate has passed.

The build-time browser gate validates direct and iframe Solar System interaction. The installer does not repeatedly launch Chromium by default because prior releases demonstrated that nested browser teardown can produce false hangs after assertions have already completed. Live deployment verification covers the shipped asset and public readiness contract.
