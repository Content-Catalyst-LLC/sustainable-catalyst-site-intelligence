# Install and test — v4.13.0

Use the packaged macOS installer with the matching release bundle. The installer verifies bundle SHA-256 hashes, creates an isolated Python environment, validates the immutable repository manifest, executes the full backend suite, performs a fast second deterministic pass, promotes the exact validated tree, then requires the live Render gate before the WordPress ZIP is considered installable.
