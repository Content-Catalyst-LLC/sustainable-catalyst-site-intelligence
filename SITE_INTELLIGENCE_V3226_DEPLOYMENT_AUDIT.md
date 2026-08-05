# Site Intelligence v3.22.9 Deployment Audit

## Problem closed

Earlier promotion scripts could stop after GitHub publication and then create an ambiguous new rollback context when rerun. Tests also wrote last-known-good state beneath the repository when invoked from the backend directory.

## Controls added

- Stable release id: `site-intelligence-v3.22.9`.
- Runtime-generated public deployment receipt.
- Expected release-id verification in the release gate.
- Atomic branch/tag publication.
- Remote-advance detection before push.
- Fixed rollback tag reused across reruns.
- Local deployment receipt with explicit lifecycle state.
- Disposable runtime sandbox during validation.
- `SC_SI_RUNTIME_STATE_ROOT` on Render.

## Remaining boundary

The package cannot deploy Render from this build environment. Live parity is established only when the macOS installer reaches the verified release gate.
