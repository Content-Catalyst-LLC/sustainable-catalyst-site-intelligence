# SI-2.1.4 — Complete historical-failure disposition

**BLOCKED — RISK-01: current-release startup recovery is nonfunctional on main-script failure.** No rebuild, code correction, new image, deployment or repeat recovery certification performed. Owner's exception excludes known critical recovery defects; it cannot cover this finding.

## Complete comparison and scope

Reparsed both original JUnit files, not only the prior summary. Untouched baseline `af0562bf278b505bf6cf083c41c9a99ff0815e73`: **368 failed / 1720 passed**. Pinned candidate `7a15666cdd1f8152272f74dd69427d810a215e3d`: **356 failed / 1746 passed**. Every candidate failed test ID appears in baseline; **zero newly failing IDs**, **12 resolved IDs**, exact lists in historical-failure-disposition.json. All 356 entries include failing assertion, test source/line, both failure messages, subsystem, concern tags and disposition. No failures were deleted, rewritten or ignored. Same-ID failure is provenance, not harmlessness. Early version assertions can mask later assertions; those later checks are not represented as passing.

| Underlying cause | Failed IDs |
|---|---:|
| Obsolete release identity expectation | 320 |
| CSS budget exceeded | 2 |
| Contradictory timing expectation | 2 |
| Historical packaging/documentation missing | 14 |
| Superseded WordPress launcher contract | 6 |
| Startup recovery release mismatch | 1 |
| Launch documentation omission | 1 |
| Current release documentation drift | 1 |
| Science asset mirror drift | 2 |
| Supply-chain diagnostic exception | 1 |
| Obsolete registry/bridge version expectation | 5 |
| Intentional economics transport contract | 1 |

## RISK-01 — release-blocking recovery defect

Related recorded failure: `backend.tests.test_offline_mobile_accessibility_performance_v2120::test_pwa_diagnostics_and_public_routes` (test line 26) reports diagnostics ok=false. Focused read-only source evaluation isolates `frontend_version_aligned=false`; this is a real current-release mismatch, not simply a stale expected value. Numerous older bootstrap/recovery identity assertions cover the same affected subsystem.

Pinned `backend/public_app/index.html:89` declares app release **4.56.1**, `app-loading`, aria-busy=true; `assets/app.css:242` hides app-loading. Loaded `assets/bootstrap-v32361.js:3-5` hardcodes **4.39.0** in the DOM selector, and init line 23 returns immediately when no matching root exists. Loaded `assets/startup-stability-v32364.js:3,26` likewise rejects a release other than **4.39.0** before installing its 1500/4500ms recovery timers. `app.js:15` reveals the app normally, so this is NOT a claim that every normal startup fails. It is loss of the independent recovery path when main app.js cannot execute (network/script error), leaving a hidden shell without either documented recovery deadline.

A network-free Node VM probe executed the exact Git-pinned scripts with a minimal DOM and deliberately absent app.js: current 4.56.1 root → **0 recovery timers, neither initializer exported, app remains hidden**; matching 4.39.0 control → recovery timers registered and shell revealed. See startup-critical-disposition-probe.json and source probe. This is deterministic focused failure-path evidence, not a browser/live-production test or a new application build. Both recovery scripts contain the same defect in the unchanged web tree too; web is not being silently fixed or replaced.

Immutable-image confirmation: an owned, network-none, read-only, cap-drop-ALL, 128MiB one-shot container read only packaged startup metadata from approved AMD64 image `sha256:69591b22b5d0a3514ee4c0922f5518cc8031b65734f0d6e969e96519c4f667eb`. Actual `/app/public_app/index.html` declares4.56.1; both actual script hashes match the probe and both declare4.39.0. Container removed via --rm; no production service, credential, image rebuild or deployment used. See pinned-image-startup-readback.json. The release Dockerfile overlays only app/data, inheriting these static assets from its pinned base; the defect is confirmed in the image, not merely inferred from checkout.

Severity disposition: **critical to the required startup-recovery guarantee; NO-GO under owner's no-critical-recovery-defect condition**. Corrective requirement: make the existing recovery scripts bind safely to the actual release DOM, verify both normal startup and main-script-failure recovery in affected backend/web packaging, and supply reviewed source/image provenance. This task expressly prohibits fixes/rebuilds; none were performed. Do not circumvent by hotpatching the pinned image, weakening the gate or asking an administrator to cut over anyway.

## Other substantive findings — not waived by age

- **Security observability:** public `/public/production-assurance/supply-chain` raises `NameError: ROOT` at `security_observability_assurance_v3310.py:77`, invoked from main.py:2427. A genuine informational security endpoint failure. The function inventories requirement metadata; it does not enforce token authentication/rate limits or change data. No auth bypass or remote execution is demonstrated by this error. Do not advertise supply-chain posture as verified. Runtime auth missing/invalid/valid-token evidence remains in native-candidate.json; no assertion of comprehensive security certification.
- **Performance:** CSS **102785 > 102000 bytes** (785-byte overrun) makes experience/performance diagnostics false; JS/HTML/total shell budgets pass source evaluation. Noncritical delivery budget issue, not a fabricated pass or measured latency guarantee.
- **Launch documentation:** launch diagnostic false solely because README lacks `/app/?view=launch`; no secret exposure evidenced.
- **Timing fixtures:** one test explicitly configures fresh_minutes=30 then expects31; browser heartbeat likewise configured30 vs expected31. No loss of state or bypass shown by those failing assertions.
- **Deployment gate:** old plugin_version4.39.0 is rejected against4.56.1; install_allowed=false is fail-closed behavior, not proof of a permissive deployment defect. SI214 uses pinned current guarded procedure, not old Render scripts.
- **Science mirrors:** real JS differences between backend and WP include tile provider/attribution and status records representation. Not identical and not certified as identical; no stored scientific records rewritten. Backend/source and frontend/WP deployment boundaries remain explicit.
- **WordPress/authority:** explicit current launch-link architecture (escaped URLs, noopener/noreferrer) replaces older fixed/eager iframe and /app/ canonical contract. Missing old iframe attributes do not establish a current iframe isolation bypass; external embed security is not universally certified by this review.
- **Economics:** direct source-attributed endpoint is intentional in current bridge; five other domains retain reliable mappings. Existing acceptance shows truthful World Bank fallback206; test assumes all six rewritten. No fabricated-health waiver.
- **Historical scripts/docs:** absent historical verifier scripts are real packaging gaps. They cannot certify this release; existing SI214 pinned image/archive/recovery/proxy evidence is the applicable path. No missing old script is silently re-created.

## Security, integrity and recovery limits

Per-ID tags identify admin/auth/security/data-truth/lineage/recovery-related tests even when the first failure is identity. No failing evidence here demonstrates token bypass, unauthorized writes, damaged state or lossy database rollback. Independent existing native token tests and exact seven-file restore/re-export evidence support only their recorded scopes. Neither source scanning nor a green test can establish absence of every vulnerability. The known RISK-01 is sufficient to fail the mandatory condition; administrator availability cannot resolve it.

## Administrator dependency

Separate secondary dependency remains: previously verified `sudo -n -l` requires interactive authentication on Contabo. No fresh availability check or service mutation was necessary after discovering RISK-01. ADMINISTRATOR-EXECUTION-SHEET.md identifies exact root-only guarded switch/inverse and ordered checkpoints. **Do not execute until RISK-01 is resolved in an authorized artifact and all conditions pass.** Existing owner deployment authorization remains recorded; no renewal requested.
