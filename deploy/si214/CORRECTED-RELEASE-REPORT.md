# SI-2.1.4 — Corrected recovery candidate and deployment readiness

2026-10-30, America/Chicago. **Corrective release gate PASSED; deployment execution BLOCKED on interactive administrator availability.** No production image replacement, writer pause, fresh capture, Caddy change or merge occurred. No SI-2.1.5 introduced. Existing owner authorization retained.

## Exact artifacts

Application source: `01ea3645617b38857f1316495f7dd0c77054a73d`. Canonical application metadata remains `backend/app/version.py` APP_VERSION **4.56.1**, release ID **SI-2.1.4**. Source archive `SI-2.1.4-corrected-source.zip`, SHA-256 `e3ff478e066ba92c7c132a5a69b4ba153588ece5c2488414fd53b2a4257029e7`.

| Artifact | Corrected AMD64 image ID | Retained rollback image ID |
|---|---|---|
| Backend | `sha256:13290390307cf61e07217c942eabb649626a6127387ba781443726b6dae2ad5d` | `sha256:89195c76cf1788b98b59b1fad669cd2c507f1d8459b9b2f967782a6cb918c207` |
| Standalone frontend | `sha256:13ba5b9fed664562765058da0e5ad1c20cf85fa3e3f6ec20faa42616709fcc43` | `sha256:3fd9e3aa84b189887c5d3a44509e5d3085301a51cf8f87ad4b39a48e9669feb9` |

Both images built sequentially on Contabo from existing immutable bases, network-disabled build, no package install/upgrade or credentials. Only the affected SI artifacts were rebuilt. Backend retains accepted app/data source from the previous candidate and overlays exactly the corrected index and two scripts. Frontend overlays exactly its index and two scripts; nginx config, other assets and runtime base preserved. Previous candidates, original images and original production containers retained. Pi development service was not replaced; no ARM production image used.

## RISK-01 correction and limits

Both `bootstrap-v32361.js` and `startup-stability-v32364.js`, in backend/public_app and web/app, now use release4.56.1 pinned to canonical APP_VERSION with permanent alignment assertions. Their exact DOM-version checks remain: a mismatched version returns without installing recovery handlers/timers. No unconditional recovery bypass. Standalone page's erroneous4.56.2 root marker is aligned with4.56.1; only the two recovery script query keys are changed for cache refresh. Other static version strings were not bulk-rewritten.

On failed primary loading/execution, existing recovery timers reveal the shell and add one accessible alert with a retry button. It explicitly warns that research data and authenticated actions may be unavailable. The explicit retry reloads only after a user click/keyboard activation; normal initialization neither adds the alert nor automatically reloads. Auth/authorization, APIs, source attribution, state formats and persistence code unchanged. Application controls requiring failed primary JavaScript are not represented as working; the usable fallback action is retry, not fabricated research functionality.

## Actually executed verification

- Permanent behavioral tests: **10 passed, 0 failed, 0 skipped**, executed on Pi Node. Covers both asset trees, metadata compatibility, mismatched-release rejection, primary load failure, primary execution exception, actual finishLaunch normal event path, visible limited shell, single retry control and explicit retry activation. Source: `tests/js/test_si214_recovery.cjs`.
- Real Chrome local browser fixtures: **6/6 passed** (backend/frontend × normal/load failure/execution failure). Normal pages reach visible `ready` with no fallback notice. Both faults reach visible `limited` with one retry notice. Backend retry keyboard activation demonstrably reloads the document; server fixture events retained. CSP prevents external connections; upstream503 fixtures truthfully label unavailable test services. This is not real-account production acceptance. Headless Chromium launch was blocked by the local sandbox; tests were completed through the existing Chrome connector instead, with no security setting changes. Screenshot: corrected-recovery-browser.png.
- Full unexcluded `python -m pytest -q backend/tests tests`: corrected **1,747 passed / 355 failed**, previous candidate **1,746 / 356**, untouched baseline **1,720 / 368**. **Zero new failing IDs** against either comparison. The formerly failing PWA diagnostic now passes; **13 baseline failures resolved**. No failure is silently excluded or labelled safe solely by age. Complete355-ID set and resolved IDs are recoverable from corrected-regression.xml/comparison and prior356-row disposition.
- Operational safeguards after SI-frontend extension: **11 passed**. Existing snapshot/hash/symlink and narrow API inverse guards plus frontend narrow/inverse/unrelated-host/wrong-upstream guards. Three production Compose services explicitly rendered with candidate/rollback profiles; loopback ports18091,18096,8091 verified. An initial unprofiled render omitted services; it was not accepted as service validation.
- Native isolated backend: health200; exact source; missing/wrong token401; valid synthetic token200; unconfigured-Core readiness503 remains truthful; three packaged assets match corrected source hashes. Native isolated frontend: healthz200 and exact corrected packaged asset hashes. Owned verifier containers removed. No production credentials, data or external networks used.
- All production service IDs/images/start times and Caddy hash unchanged during native verification. Existing administrator preflight still fails without interactive authentication. Earlier live-state recovery certification remains PASS and was not repeated. Pi kernel warned that requested container memory limits are unsupported; limits are NOT claimed enforced. Regression used one CPU/one concurrent test container and completed; no simultaneous Pi image builds.

Known-critical disposition: **RISK-01 CLOSED for these corrected artifacts**, on behavior plus actual-image hash evidence. Prior security-assurance `ROOT` diagnostic exception, CSS budget overrun and science/WP mirror drift remain real disclosed noncritical limitations as analysed in HISTORICAL-FAILURE-DISPOSITION.md; no universal security certificate or full green suite is claimed. No known remaining critical auth, state-integrity or recovery defect identified within the reviewed scope. The355 historical exceptions remain conditional on actual production acceptance; abort on new security/data impact.

## Recovery artifacts and current production

Corrected images preserved on designated Pi SSD in `/mnt/catalyst-ssd/backups/site-intelligence/SI-2.1.4/corrected-images-01ea3645.tar`: **103,002,112 bytes**, SHA-256 **cf63cc5d56213e1cb2f022ad2acb22492c35df0503482caefd962c409b229c66**. Relay/Pi hashes, OCI descriptors, Docker load and exact AMD64 IDs verified; images not executed on ARM. Previous image archive and seven-file actual-state checkpoint remain intact. No secrets/mounted credentials/live state included in new image archive.

Production remains original backend89195c76 and frontend3fd9e3aa, original Caddy routing8091/8096. Latest isolated acceptance records Caddy and all service starts unchanged, not a claim that corrected candidate is publicly deployed. Original public readiness baseline was503 domain-degraded. A new503 is not automatically a product failure if truthful, but no newly degraded domain is accepted. The prepared switch guard still requires candidate ready200/ready=true; if it refuses, stop instead of bypassing it.

## Exact deployment sequence — not yet executed

Staged tools: `/home/catalystadmin/si-2.1.4-release/correction-01ea3645`. Administrator must be available in their own interactive Contabo terminal for switch AND inverse before writers are paused. No password is requested or captured. **Stop here until available.** The existing deployment authorization does not create sudo privileges.

Then: fresh SI-only graceful drain → frozen seven-file snapshot → source/relay/Pi hash+metadata verification → seed candidate static app-data and overlay only fresh runtime files into shared app-data/backend-data → authenticate/verify candidate and all six truthful domains → guarded atomic SI API+frontend proxy switch → public/auth/data acceptance → shared-state rollback on failure. The original frontend remains running on8096 throughout; no restart required. Fresh state receipt required because production resumed after earlier backup. Do not fill flags to bypass actual work.

```bash
cd /home/catalystadmin/si-2.1.4-release/correction-01ea3645
export SI214_IMAGE=sha256:13290390307cf61e07217c942eabb649626a6127387ba781443726b6dae2ad5d
export SI214_WEB_IMAGE=sha256:13ba5b9fed664562765058da0e5ad1c20cf85fa3e3f6ec20faa42616709fcc43
export SI214_STATE=/home/catalystadmin/si-2.1.4-release/state/active
# Run ONLY after fresh snapshot, Pi verification, state seeding and real current receipt.
python3 guarded_proxy_switch.py --plan corrected-deployment-plan.json --receipt corrected-state-receipt.json --direction deploy --check-state-only &&
 docker compose -p site-intelligence-si214 -f production.compose.yml up -d --no-deps --no-build --wait --wait-timeout 120 site-intelligence-si214 site-intelligence-web-si214
# Candidate auth/data/domain/routing verification checkpoint; only then authorized administrator:
sudo python3 guarded_proxy_switch.py --plan corrected-deployment-plan.json --receipt corrected-state-receipt.json --direction deploy --execute
```

The updated guard verifies corrected frontend image, health and exact three recovery asset hashes. It atomically patches ONLY API8091→18091 and SI frontend8096→18096 in the same validated Caddy update. It preserves all unrelated blocks; administrator Caddy validation/reload remains mandatory. Record `proxy_after_sha256` in the actual receipt. Expired BLOCKED receipt remains unusable; owner authorization is not falsely represented as a fresh snapshot verification.

Rollback after any candidate writes: gracefully drain only corrected backend, retain new writes in the same active dirs, verify no SI dual writer, launch old backend image against shared state, verify old backend/auth/state and original frontend; inverse both SI routes. Never restart stale original layer over candidate writes.

```bash
# Same directory and exported variables. Candidate already safely quiesced.
python3 guarded_proxy_switch.py --plan corrected-deployment-plan.json --receipt corrected-state-receipt.json --direction rollback --check-state-only &&
 docker compose -p site-intelligence-si214 -f production.compose.yml up -d --no-deps --no-build --wait --wait-timeout 120 site-intelligence-si214-rollback &&
 sudo python3 guarded_proxy_switch.py --plan corrected-deployment-plan.json --receipt corrected-state-receipt.json --direction rollback --execute
```

If proxy never switched, leave existing routes alone; start shared-state old backend on8091 and keep original frontend8096. Before any candidate has run/written, abort by restoring original restart policy and starting untouched original SI. Do not pause/restart Lab, Core, Workspace, Library, WordPress or any other service. No PR merge. Any missing recovery file, hash/auth failure, new domain degradation, proxy drift or unrelated impact aborts/rolls back. Administrator sheet lists exact sudo checkpoints.

**Final readiness: corrected candidate technically verified; controlled production execution BLOCKED solely on authorized interactive administrator availability and the consequent unexecuted fresh cutover checkpoints.** No deployment timestamp exists because no deployment occurred.
