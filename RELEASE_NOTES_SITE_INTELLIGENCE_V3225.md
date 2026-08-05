# Site Intelligence v3.22.5 Release Notes

## Deployment Gate, Live Parity Lock, and Rollback Readiness

This release closes the gap between packaging a backend and proving that Render is serving it.

### Delivered

- `/public/release-gate` evaluates WordPress compatibility, Render branch, Git commit, release channel, and deployment identity.
- `/health`, `/public/build-info`, `/public/deployment-status`, and `/public/release-gate` are explicitly uncacheable.
- Build information now includes a 20-character release fingerprint.
- WordPress displays the gate state, Render commit, and fingerprint in admin diagnostics.
- Healthy WordPress parity is rechecked every 15 minutes; blocked parity is rechecked every 45 seconds.
- The GitHub/Render promotion script creates an annotated rollback tag before deployment.
- The installer withholds the WordPress handoff until Render reports the exact pushed commit and `install_allowed=true`.

### Safety boundary

The workflow does not silently rewrite Git history or automatically roll back production. It preserves a rollback tag and prints the exact prior-commit Render deployment command for an operator-controlled rollback.
