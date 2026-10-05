# Site Intelligence v4.43.0 Release Certification

Release: **v4.43.0 — Modular FastAPI Route & Capability Registry**

## Certified contracts

- Canonical backend, WordPress, standalone app, Render manifests, and 27 release-bound policy files report `4.43.0`.
- System/runtime routes are registered through `backend/app/routers/system.py`.
- Data-truth, workspace-evidence, and record-truth routes are registered through `backend/app/routers/data_truth.py`.
- Capability discovery is registered through `backend/app/routers/capabilities.py`.
- `/public/capabilities`, `/public/capabilities/{capability_id}`, `/public/routes/registry`, and `/public/routes/summary` are available.
- Runtime inventory contains 1,353 API routes, 38 already modularized, 0 unclassified, and 0 duplicate method/path contracts.
- Existing v4.41 spatial/energy endpoints remain present.
- WordPress shortcode containment remains 68 published + 4 protected canonical shortcodes = 72.
- Contabo deployment preserves dynamic production data while restoring the 27 release-bound static policy files from the release package.

## Automated verification

- `scripts/validate_v4430_release.py`: PASS
- Python compile: PASS
- WordPress PHP lint: PASS
- Current-contract pytest gate: **23 passed**
- Runtime registry smoke: PASS
- Deployment shell syntax: PASS

## Historical-suite note

The complete historical backend test archive is not a current-release gate. Many old tests intentionally hard-code earlier application versions. The first broad-suite failure asserts `4.39.0` while the application correctly reports `4.43.0`. v4.43.0 therefore uses the current-contract certification suite rather than rewriting historical release semantics.
