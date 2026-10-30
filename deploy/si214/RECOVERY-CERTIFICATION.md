# SI-2.1.4 — Recovery certification and deployment approval

> Final disposition supersedes earlier status: BLOCKED on RISK-01, startup recovery release mismatch confirmed in pinned image. Owner authorization retained. See HISTORICAL-FAILURE-DISPOSITION.md and ADMINISTRATOR-EXECUTION-SHEET.md. No deployment permitted while this mandatory condition fails.

> Current deployment attempt: owner authorization received; BLOCKED on administrator execution access before any mutation. See DEPLOYMENT-STATUS.md. Earlier approval-pending text below is historical and superseded.

**Recovery gate PASS. Production deployment NOT AUTHORIZED.** Application source remains `7a15666cdd1f8152272f74dd69427d810a215e3d`; no new numbered build or image replacement.

## Executed maintenance

Owner-authorized SI-only window, 2026-10-29 UTC. Quiescence requested **17:43:36.971688**, consistent snapshot complete **17:43:44.148374**, original service health verified **17:43:55.286281** (18.315 seconds including drain/copy/resume verification; exact externally observed outage not measured). Restart policy temporarily changed from `unless-stopped` to `no`; SIGTERM sent to the single SI Uvicorn process, clean shutdown marker verified, exit 143, no force-kill. Only original `sc-site-intelligence` was stopped/started. Original ID/image/configuration and restart policy preserved. Two frozen reads of every file matched. Original writable layer was never replaced or modified by restoration.

Seven runtime files total **26,172,272 bytes** at capture; earlier 24,955,822-byte inventory was a different observation, not a fixed expected length. Archive **26,183,680 bytes**, SHA-256 `85a86dee9139004f497d5e91e606e62e8f61cf5c1fe164fde0c5f7dbccced59f`. Per-file hashes/uid/gid/mode/mtime/size are in recovery-certification.json. No mounted credential, env file, private key or unrelated application data was included.

Restricted Pi destination: `/mnt/catalyst-ssd/backups/site-intelligence/SI-2.1.4/recovery-20261029T174332Z/live-state.tar`; directory 0700, archive 0600. Source, streaming relay and Pi SHA matched. No plaintext state bodies were written to the Mac. The restricted temporary Contabo recovery directory `/home/catalystadmin/si-2.1.4-release/recovery-20261029T174332Z` is retained for recovery; do not publish its archive or discard it automatically.

## Isolated restoration and rollback evidence

Restored actual snapshot into two disposable Pi containers, network `none`, CPU 1, memory 512 MiB, no production credentials, no ports or shared production mounts. All seven file hashes, lengths, uid/gid/mode and timestamps matched; all JSON/JSONL parsed; 8,148 Core queue rows and 16,868 operations-history rows validated without replay. Country-cache loader reported no read error. Re-export of both restorations preserved bytes and metadata. Both containers removed. Recovery archive and receipts retained.

Pi executed candidate ARM image and previous ARM image with all six relevant state writer/parser modules verified byte-identical to actual production and candidate. **This is file restoration plus compatible-parser rollback verification, not execution of the AMD64 production image on ARM or a public deployment test.** Actual AMD64 old backend, candidate and frontend images remain preserved and Docker-load verified on Pi. No schema/state migration is introduced.

Before candidate writes, the tested maintenance rollback is restoring `unless-stopped`, starting the untouched original container, then verifying health/readiness and unchanged configuration. This was executed successfully. After candidate writes, deployment rollback must drain candidate and use pinned old image with the SAME persisted active directories, preserving new writes; never restart the old frozen writable layer as if it contained those writes. Existing proxy inverse is narrowly guarded and has nine previously passing guard tests, not a live production cutover test.

## Lab and protected services

Read-only inspection identified `sc-lab-health-watch.timer` → `sc-lab-health-watch.service` → `/usr/local/sbin/sc-lab-health-recover`. Its only restart target is `sc-lab` and its trigger is Lab's own unhealthy status, with 300-second cooldown. Script SHA-256 `f6519d91ecd0af66dffc27cf20a4e1256e27cd266042d22cd9e1848890964682`. Both Compose projects have no declared dependencies; health checks target their own 8091/8092 ports; no container mounts the Docker socket. This rules out the identified controller and declared topology as an SI lifecycle dependency. Earlier Lab restart's individual trigger remains unattributed; no claim that it was caused by SI. Lab and every other protected container retained IDs/images/start times throughout this maintenance and final verification. No watchdog changes made.

Public app HTTP 200; production API health HTTP 200. Production readiness remains its pre-window HTTP 503 `domain-degraded`, ready false. This is preserved baseline behavior, **not healthy readiness or production certification of the candidate**. Authentication configuration hash and Caddy SHA-256 `3d5202c2b6a3ae0859db31e05a34cbdb77380243984bb626da73765fb58b7b8c` unchanged.

## Approval requested — deployment remains stopped at this gate

Approve a separate SI-only deployment window for the pinned AMD64 image, a fresh consistent capture/transfer (production resumed and has continued writing), state-directory seeding, candidate start on loopback 18091, and the guarded API-only Caddy switch 8091→18091 by an authorized administrator. Approve the shared-state rollback below. Frontend, Lab, Core, Workspace, WordPress, databases and unrelated services must remain untouched. No PR merge is needed or requested as part of cutover.

Explicit risk decision: unexcluded regression **1,746 passed / 356 failed**, baseline **1,720 passed / 368 failed**; **zero newly failing IDs**, 12 resolved. The 356 retained historical failures mean the suite is not green. Accept that disclosed residual risk or require remediation before deployment. Candidate readiness must independently pass on production configuration before any proxy switch; otherwise abort and restore original service.

Exact pinned deployment and rollback commands are in RELEASE-REPORT.md. The expired `state-receipt.BLOCKED.json` remains blocked. This recovery authorization is never substituted for deployment approval. A new approved, short-lived receipt must reference a fresh frozen snapshot, matching active-state overlay and this Pi recovery evidence. Proxy execution requires the authorized host administrator; audit account has no passwordless sudo. Do not run commands partially or leave original SI stopped if a prerequisite fails.
