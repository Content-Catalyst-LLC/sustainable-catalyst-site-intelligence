# Site Intelligence v1.20.1 — Backend Compatibility Check and Admin Cache Reliability Patch

This maintenance release prevents stale WordPress build-information transients from preserving an obsolete plugin/backend mismatch after a successful Render deployment.

## Cache policy

- Matching versions: 21,600 seconds
- Mismatches: 45 seconds
- Unavailable or invalid responses: 30 seconds

Cache keys include both the normalized backend URL and current plugin version. Legacy unversioned `scsi_build_info_*` transients are removed on activation, upgrade, and settings save.

## Administrator workflow

The Site Intelligence settings page displays the checked backend URL, plugin version, returned backend version, HTTP response state, verification state, and last verification time. Administrators can use **Refresh backend version** to bypass the transient and request fresh build information immediately.

## States

- `match`
- `mismatch`
- `unavailable`
- `invalid-response`
- `not-configured`

A temporary verification failure does not claim that a known mismatch exists. Platform Core remains optional and no paid dependency is introduced.
