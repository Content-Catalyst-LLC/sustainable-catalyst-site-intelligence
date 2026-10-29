# SI-2.1.4 — Consolidated release and deployment preparation

2026-10-29, America/Chicago. **Recovery gate PASS; production execution awaits separate approval and explicit acceptance of 356 historical failures.** Application source candidate is consolidated and running in Pi development. Original production Site Intelligence was gracefully restarted only for the authorized recovery window; no candidate was deployed. No new numbered release was introduced.

## Verified candidate

- Source commit `7a15666cdd1f8152272f74dd69427d810a215e3d`; package SHA-256 `a63f172784f1208d1d021c68d6ab33ab81668deadc2e822672e35b798431f816`. SI-2.1.1–SI-2.1.4 application corrections are consolidated under release ID SI-2.1.4, retaining application/schema version 4.56.1.
- ARM64 image `sha256:39f53215867c34880d1c5b9e36508112c7571d55116cf79de9d7e7e10edfb842` runs as `sc-site-intelligence-dev` on Pi loopback 8091. Three original Compose files are byte-unchanged, including `compose.pi-core-read.yml`; original data mount preserved. All protected Pi containers retained IDs/images/start times.
- Native AMD64 candidate `sha256:69591b22b5d0a3514ee4c0922f5518cc8031b65734f0d6e969e96519c4f667eb` built from pinned production runtime base, without package upgrades, secrets or live state. Isolated native smoke verified 351 static source/reference files, liveness, exact source/release ID, missing/invalid token 401, synthetic valid token 200 and truthful unconfigured-Core readiness 503. Temporary native test container removed. This is not public production acceptance.
- Route inventory: 1,530 unique registrations, 33 capabilities, 216 modular routes, zero unclassified. The five `/v1/energy-spatial` routes were introduced in tracked commit `c6712618` before the stale assertions. Their existing infrastructure-energy ownership and public read-only/request-local POST contract are unchanged. All 12 count assertions plus registry reconciled; no extra routes/security exposure added.
- Route-exposure audit covers all 1,530 registrations: 331 production-token dependencies, 128 handler-level auth hints and 1,071 with no token guard detected by static dependency/handler inspection. Static classification is not a proof of every handler; the deployed require_token AST matches the candidate and native auth negatives/positives passed. No auth registrations changed in SI-2.1.4.
- Economics: deterministic tests preserve legitimate World Bank fallback 206 and invalid/unavailable dependency 503; failed dependencies are never relabelled healthy. Source-attribution metadata remains bounded; direct fallback identifies World Bank. No data fabricated.

## Actual test evidence — no exclusions

Full command: `python -m pytest -q backend/tests tests`. Candidate: **1,746 passed, 356 failed**. Untouched af0562bf baseline: **1,720 passed, 368 failed**. Failure-ID comparison: **12 resolved, zero newly failing IDs, 356 confirmed pre-existing failures**, detailed in regression-comparison.json/candidate-failures.json. These include obsolete release identity/packaging and older asset/contract assertions; no blanket version rewrite or silent exclusion. Do not describe the full suite as green. Initial collection failed because runtime lacked httpx; pinned test-only dependency corrected the isolated test environment. Runtime requirements were not upgraded.

New operational proxy/snapshot guards: **9 tests passed** (narrow patch/inverse, duplicate/wrong/multiple-upstream refusal, snapshot completeness/hash/scope/symlink handling). Production Compose rendered successfully with `--no-env-resolution`; real environment values were not emitted. Authorized production drain/snapshot/resume and isolated actual-state Pi restoration now passed; see RECOVERY-CERTIFICATION.md. No proxy switch or candidate production deployment executed.

Pi live candidate: `/health` 200; `/ready` 200 with **domain-partial**, Core connected. Kenya probes:

| Domain | HTTP | Actual classification / records |
|---|---:|---|
| Economics | 206 | World Bank source-fallback, 2 records |
| Law | 200 | Connected, 0 records |
| Science | 200 | Connected, 0 records |
| Humanitarian | 206 | Partial-live, 0 records; ReliefWeb configuration required |
| Resources | 200 | Connected, 0 records |
| Dossiers | 206 | Partial records, 11 evidence records |

Counts are observed query results, not guaranteed future coverage. Empty connected queries are not unavailable; partial upstream coverage remains partial. Production access checks used only synthetic credentials in isolation. Pi Core write/public keys and Google credential settings are empty; development API token differs from production (ephemeral HMAC comparison, no token/digest retained). Pi and Contabo remain separate; no ARM64 image deployed to AMD64 production.

## Production mechanism, rollback assets and differences

Existing backend: `sc-site-intelligence`, image `sha256:89195c76cf1788b98b59b1fad669cd2c507f1d8459b9b2f967782a6cb918c207`, production Compose `/opt/sustainable-catalyst/site-intelligence/compose.yml`, loopback 8091. Existing frontend: `sc-site-intelligence-web`, image `sha256:3fd9e3aa84b189887c5d3a44509e5d3085301a51cf8f87ad4b39a48e9669feb9`, loopback 8096. Public API `site-intelligence-api.sustainablecatalyst.com` proxies 8091; public app `intelligence.sustainablecatalyst.com` proxies 8096. Existing API reports 4.56.1 and unavailable Git revision; host checkout is d370a3b5. Do not equate that checkout with every deployed byte. Rollback is pinned to the actual running image, not an inferred source checkout.

The Pi now holds `/mnt/catalyst-ssd/backups/site-intelligence/SI-2.1.4/immutable-images.tar`: **102,929,920 bytes**, SHA-256 `46c67d321e08041b85f978a35b36522fd45c3fffd7538ee5c86fda62469ed2cb`. It contains old backend, unchanged frontend and candidate AMD64 images. Relay/destination SHA matched; OCI descriptors verified; Pi Docker image load and all three image IDs/architectures verified. Images were not executed on ARM64. Mounted credentials and writable layers are absent. Initial archive verification assumed legacy config IDs; corrected OCI descriptor handling passed. This certifies immutable image recovery only.

Development uses .env.dev, no production Google/write credentials, loopback and existing Core-read overrides. Production proposal extends the EXISTING production Compose, reuses its protected env/credential paths, and uses a separate service/project/loopback port plus persistent state directories. It never deploys Pi overrides. No database, DNS, package, PHP/PostgreSQL/Docker or unrelated service change is included. Frontend unchanged: no web-image replacement needed.

## Recovery gate closed; separate deployment approval required

See RECOVERY-CERTIFICATION.md and recovery-certification.json for actual snapshot, Pi integrity/restore, unchanged configuration/protected services and limitations. The seven files are preserved; original SI resumed. Production baseline readiness remains HTTP 503 domain-degraded. No image, proxy or authentication change occurred.

Because writers resumed, future deployment MUST capture a fresh frozen snapshot and copy the latest seven files to new active directories; the certified archive is a recovery checkpoint, not permission to discard subsequent writes. Keep static candidate references in app-data, and overlay only authorized runtime files. Require owner deployment approval, accepted historical-test risk, administrator proxy access and target readiness before switching. On any pre-cutover failure, restore original restart policy/start/health; after candidate writes, preserve shared state and use old-image rollback.

## Exact guarded target commands — NOT APPROVAL TO EXECUTE

Staging directory: `/home/catalystadmin/si-2.1.4-release`. After separate deployment approval, fresh writer quiescence and active-state seeding are evidenced, install the supplied deployment-plan.json and approved state-receipt.json there. Review script hashes/authority independently; JSON flags alone are not proof of human approval. State receipt must bind source, expiry, original container, complete immutable snapshot paths/checksums, protected Pi archive/restore, writer quiescence and rollback compatibility. Global operations/config changes must be frozen for the narrow switch.

```bash
cd /home/catalystadmin/si-2.1.4-release
export SI214_IMAGE=sha256:69591b22b5d0a3514ee4c0922f5518cc8031b65734f0d6e969e96519c4f667eb
export SI214_STATE=/home/catalystadmin/si-2.1.4-release/state/active
# Old SI must already be safely quiesced; the receipt/paths must be real and verified.
python3 guarded_proxy_switch.py --plan deployment-plan.json --receipt state-receipt.json --direction deploy --check-state-only &&
 docker compose -p site-intelligence-si214 -f production.compose.yml up -d --no-deps --no-build --wait --wait-timeout 120 site-intelligence-si214 &&
 sudo python3 guarded_proxy_switch.py --plan deployment-plan.json --receipt state-receipt.json --direction deploy --execute
```

The guard checks exact host/images/source/target health/readiness, no previous active writer, immutable snapshot hashes and baseline Caddy hash. Only the API block changes 8091→18091, validated then replaced atomically with a Caddy reload. No whole-file old backup is blindly restored over other projects. A consistent state capture may require a short SI API interruption; zero downtime is NOT promised and duration is unmeasured. Do not leave the service stopped if the owner-approved procedure aborts; use the approved rollback that preserves current state. Recovery gate is closed; separate deployment approval and explicit historical-test risk acceptance are now requested. A new consistent cutover snapshot is still mandatory because production has resumed.

Rollback AFTER a completed switch: first gracefully quiesce only the candidate using the separately approved drain procedure; verify it is stopped and preserve all new writes in the shared state directory. Do not restart the frozen original container against stale private state. With the independently verified shared-state format and receipt, the old image runs against the same persisted data:

```bash
cd /home/catalystadmin/si-2.1.4-release
# Set the same SI214_IMAGE/SI214_STATE values above; candidate must already be safely stopped.
python3 guarded_proxy_switch.py --plan deployment-plan.json --receipt state-receipt.json --direction rollback --check-state-only &&
 docker compose -p site-intelligence-si214 -f production.compose.yml up -d --no-deps --no-build --wait --wait-timeout 120 site-intelligence-si214-rollback &&
 sudo python3 guarded_proxy_switch.py --plan deployment-plan.json --receipt state-receipt.json --direction rollback --execute
```

Record the successful deployment guard's `proxy_after_sha256` in the approved receipt before rollback. The inverse changes only 18091→8091. If deployment aborted BEFORE the proxy switch, the API block already targets 8091: start the approved old-image rollback service on 8091, verify it and do not call an inverse for a switch that never happened. Any unexpected image/config/schema/hash, missing backup, concurrent writer or failed readiness aborts. Preserve snapshots and original stopped container; no destructive database downgrade, original data overwrite or unrelated restart.

## Protected-service evidence and final decision

Recovery certification passed; exact maintenance receipt and final public checks are retained. Original SI container/image/authentication and Caddy preserved. All unrelated containers retained IDs/images/start times during this maintenance. The separate Lab health watchdog has no SI dependency; earlier restart trigger remains unattributed. No production candidate deployment or public candidate acceptance is claimed.

**BLOCKED for production execution pending owner deployment approval, explicit acceptance/remediation of the 356 historical failures, and authorized administrator availability for the guarded proxy switch.** Fresh capture/state seeding are required operations inside that later approved deployment window. No technical recovery artifact remains missing. Verify public app/API, readiness, Core, six domain classifications/source/record availability and auth boundaries after approved cutover; abort to shared-state rollback on failed acceptance.
