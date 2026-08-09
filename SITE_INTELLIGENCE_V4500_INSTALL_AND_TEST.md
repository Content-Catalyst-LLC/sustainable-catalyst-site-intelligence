# Site Intelligence v4.8.0 — Install and Test

Use the release-bundle installer rather than manually copying repository files.

The installer verifies bundle SHA-256 checksums, extracts the exact repository ZIP, creates an isolated Python virtual environment, installs backend and development requirements, runs the deterministic v4.8.0 verifier, performs a fast second deterministic pass, promotes the exact validated source through GitHub/Render, and waits for the live release gate.

The live gate checks Global Ocean Intelligence independently from the inherited Orbital Earth, Lunar & Planetary, Astronomical Observation, and Solar System contracts. It requires the Ocean overview, catalog, readiness contract, and shipped `ocean-surface-v4500.js` asset before reporting success.

The WordPress ZIP should be installed only after the installer reports that the exact v4.8.0 GitHub/Render live gate has passed.

The focused build-time browser gate validates direct and iframe Ocean Surface interaction. The installer does not repeatedly launch Chromium by default; live deployment verification checks the shipped asset and public readiness contract.
