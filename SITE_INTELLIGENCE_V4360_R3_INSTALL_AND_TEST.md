# Site Intelligence v4.36.0 R3 — Install & Test

Use the R3 release bundle on macOS. The installer verifies checksums, creates an isolated virtual environment, runs the deterministic suite, runs browser certification in Chrome/Chromium, promotes the exact validated tree to GitHub, waits for Render release identity, and prints the WordPress plugin ZIP path.

## Expected release gates

- static release validation: PASS
- immutable manifest verification: PASS
- deterministic pytest suite: 1,677/1,677
- Science with Platform Core unconfigured: Earth / Ocean / Space available
- Science→Ocean: hydration state `ready`, 11 marine cards
- Space: six local launch modules available
- Ocean standalone browser gate: 11 systems / 5 groups
- country identity and evidence gates: PASS
- desktop/mobile/iframe: 35/35 routes ready or explicitly degraded
- Git tag: `v4.36.0-r3`

## WordPress

After backend promotion, upload the R3 WordPress plugin ZIP and choose **Replace current with uploaded**. WordPress runtime version remains `4.36.0`, so the administrative version number alone will not distinguish R3 from earlier repairs.
