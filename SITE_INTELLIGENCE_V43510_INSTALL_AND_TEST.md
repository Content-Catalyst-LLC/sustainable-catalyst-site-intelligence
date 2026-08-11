# Install and test — Site Intelligence v4.35.10

Place the release bundle and deployment script in `~/Downloads`, then run the deployment script. The installer verifies SHA-256 bundle checksums, creates an isolated Python virtual environment, runs deterministic validation, reruns static/browser validation, and promotes through GitHub and Render using first-party release-integrity gates. External API availability is reported separately and does not block deployment.
