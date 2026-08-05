# Site Intelligence v3.22.8

## Render Deployment Parity and Release Promotion

This release repairs the release process that previously validated local artifacts and updated the WordPress plugin without promoting the backend source to the Git branch connected to Render.

### Deployment corrections

- Adds an explicit Render `autoDeployTrigger: commit` contract.
- Adds `/health` as the Render health-check path.
- Uses explicit Python module invocation for build and start commands.
- Adds a deployment promotion script that validates, clones the canonical GitHub repository, synchronizes the release, commits, tags, pushes, and verifies the live Render commit.
- Supports Render auto-deploy, a secret deploy hook, or the authenticated Render CLI.
- Blocks WordPress promotion until backend version and Git commit parity are confirmed.

### Runtime visibility

- Extends `/public/build-info` with public-safe Render service, branch, repository, commit, instance, and external URL metadata.
- Adds `/public/deployment-status` for release and deployment verification.
- Includes the Render commit SHA in support diagnostics without exposing credentials or environment secrets.

### Release boundary

The backend is not considered upgraded merely because a repository ZIP or WordPress ZIP was created. A release is complete only after the canonical Git branch contains the release commit and the live Render build-info endpoint reports the same version and commit.
