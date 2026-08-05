# Site Intelligence v3.22.9

## Resume-Safe Promotion, Deployment Receipts, and Runtime-State Isolation

This release makes the GitHub-to-Render promotion path resumable and auditable. It adds a runtime deployment receipt endpoint, verifies a stable release identifier, isolates writable last-known-good state from the immutable checkout, uses atomic Git ref publication, preserves one rollback point across retries, and writes a local machine-readable promotion receipt.

No live deployment is claimed by the package itself. The macOS deployment installer validates locally, promotes to GitHub, waits for Render, and releases the WordPress ZIP only after the live gate verifies the exact version, release id, and commit.
