# Site Intelligence v3.22.6 deployment audit

## Confirmed failure

The v3.22.1 through v3.22.3 terminal installers extracted release bundles, installed dependencies, ran validation, and printed the WordPress ZIP path. They did not synchronize the release into the canonical Git repository, create a commit, push the connected branch, or trigger and verify a Render deployment.

As a result, WordPress could report a newer plugin version while the Render backend continued serving an older commit.

## Corrective architecture

v3.22.6 establishes a single promotion sequence:

1. Verify the immutable repository manifest and full test suite.
2. Clone `Content-Catalyst-LLC/sustainable-catalyst-site-intelligence` from GitHub.
3. Resolve the repository's connected default branch.
4. Synchronize the exact release tree without copying virtual environments, caches, or Git metadata.
5. Re-run validation against the exact Git tree.
6. Commit and tag v3.22.6.
7. Push the branch and release tag.
8. Trigger Render through auto-deploy, a configured deploy hook, or the authenticated Render CLI.
9. Poll `/public/build-info` until both release version and `RENDER_GIT_COMMIT` match the pushed commit.
10. Expose the WordPress ZIP only after backend parity succeeds.

## Render configuration hardening

- `autoDeployTrigger: commit`
- `healthCheckPath: /health`
- `python -m pip` build invocation
- `python -m uvicorn` start invocation

## Public deployment evidence

`/public/build-info` and `/public/deployment-status` now report public-safe deployment metadata supplied by Render, including service name, service ID, external URL, repository slug, branch, commit, instance ID, release version, and health-check contract.

No Render API key, deploy hook, GitHub token, or application secret is exposed by these endpoints.
