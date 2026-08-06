# Site Intelligence v3.23.6.1

## Single-Owner Bootstrap and Loading Recovery

This emergency patch repairs the v3.23.6 condition in which the correct Render release could remain behind the **Opening Site Intelligence** overlay.

### Repairs

- Adds `bootstrap-v32361.js` as the only service-worker registration owner.
- Removes direct service-worker registration and controller-change listeners from `app.js`, `performance-offline-v3236.js`, and `experience-v2120.js`.
- Keeps service-worker installation optional and non-blocking.
- Adds one guarded update activation and one guarded controller-change reload path.
- Adds a nine-second startup deadline that opens a limited workspace instead of leaving the launch screen permanent.
- Wraps the complete application initialization in a fail-open recovery boundary.
- Prevents optional imagery, event, country, or public-data failures from blocking the visible application.
- Moves responsive iframe-height listeners inside the application closure, eliminating a browser `reportHeight is not defined` error.
- Adds `/public/bootstrap-recovery` and includes the bootstrap asset in runtime health and the offline shell.
- Preserves the WordPress host-isolation repair; application bootstrap code is not executed in the WordPress host document.

### Production boundary

The patch does not claim that third-party imagery or public feeds are always available. When optional services fail, the active workspace opens in a clearly limited state and retains local geography and recovery controls.
