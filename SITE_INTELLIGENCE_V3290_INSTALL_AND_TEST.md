# Site Intelligence v4.1.0 Install and Test

Use the release bundle and macOS installer together. The installer verifies bundle checksums, creates an isolated Python environment, runs two deterministic validation passes, promotes the exact Git tree to GitHub and Render, verifies the live v4.1.0 release gate, and then reports the WordPress ZIP to install.

The WordPress ZIP should not be installed before the live gate succeeds.
