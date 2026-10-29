# SI-2.1.4 — Contabo administrator execution sheet

**HOLD: DO NOT EXECUTE.** Historical-failure disposition is BLOCKED on RISK-01, the pinned candidate's startup-recovery release mismatch. Administrator access alone does not clear this gate. No rebuild, new image, hotpatch or merge is authorized in this task. Existing owner deployment authorization is recorded; do not request renewed general approval.

Host: `vmi3544820` / `94.72.113.77`. Audit/deployment account: `catalystadmin`. Working directory: `/home/catalystadmin/si-2.1.4-release`. Relevant services only: original `sc-site-intelligence`, proposed `sc-site-intelligence-si214`, rollback `sc-site-intelligence-si214-rollback`. Existing frontend `sc-site-intelligence-web` remains untouched.

Pinned approved application: `7a15666cdd1f8152272f74dd69427d810a215e3d`.

| Artifact | Exact immutable image ID |
|---|---|
| Candidate AMD64 | `sha256:69591b22b5d0a3514ee4c0922f5518cc8031b65734f0d6e969e96519c4f667eb` |
| Original/rollback AMD64 | `sha256:89195c76cf1788b98b59b1fad669cd2c507f1d8459b9b2f967782a6cb918c207` |
| Unchanged frontend | `sha256:3fd9e3aa84b189887c5d3a44509e5d3085301a51cf8f87ad4b39a48e9669feb9` |

## Interactive administrator requirement

Administrator authenticates directly in their own Contabo terminal. No password goes into chat, scripts, environment variables, files, logs or GitHub. No sudo permission changes, Docker-based host privilege bypass, general root shell or package upgrade is requested. Previous read-only preflight: `sudo -n -l` → password required. No new availability assertion is made.

Only these two top-level operations require interactive sudo in the prepared procedure:

```bash
# Deployment switch — ONLY after every prior checkpoint passes.
cd /home/catalystadmin/si-2.1.4-release
sudo python3 guarded_proxy_switch.py --plan deployment-plan.json --receipt state-receipt.json --direction deploy --execute

# Inverse rollback — ONLY after candidate drain and shared-state old-image verification.
sudo python3 guarded_proxy_switch.py --plan deployment-plan.json --receipt state-receipt.json --direction rollback --execute
```

The reviewed tool internally runs Caddy validation, preserves config mode/ownership, atomically replaces only the exact guarded SI API configuration, and invokes `systemctl reload caddy`. Deploy changes SI API upstream 8091→18091; inverse changes 18091→8091. Caddy reload is a shared-proxy operation but its configuration diff must be SI-only. Do not run a separate unguarded `sed`, whole-file restore, reload/restart or proxy cutover. If validation/reload fails, the helper reverses only its own unchanged configuration bytes. Authorized administrator must also be available for that failure path.

## Required sequence — coordinated execution only after technical gate clears

1. **Preflight:** close RISK-01 against an explicitly authorized artifact; do not silently replace these pinned IDs. Verify host/container IDs, both image IDs/architecture/revision, existing env/credential references and authentication hash, current Caddy hash, and protected-service baseline. Confirm the administrator is available for switch AND inverse before pausing any writer. Do not touch Lab/Core/Workspace/Library/WordPress.
2. **Fresh consistent capture:** dry-run existing helper against exact original SI container, temporarily set only its restart policy to no, SIGTERM only its single Uvicorn process, bounded wait and require clean-shutdown marker; no forced kill. Capture exactly seven allowlisted files while frozen. Produce fresh per-file SHA256/size/uid/gid/mode/mtime, read twice to confirm consistency, preserve original layer/container. Keep original stopped only inside this coordinated cutover; on abort before candidate starts, restore original restart policy and operation immediately.
3. **Pi preservation:** stream only that fresh state archive to a unique mode0700 directory under `/mnt/catalyst-ssd/backups/site-intelligence/SI-2.1.4`, archive0600. Verify source/relay/Pi SHA, completeness, metadata and fresh-receipt binding. Existing prior restoration certification remains valid for unchanged tooling/format; do not repeat it indiscriminately or call an older checkpoint the latest state. If checksum/scope mismatch occurs, abort. No credentials or private-key copies.
4. **Seed active state:** create new restricted snapshot and active roots. Seed app-data static reference files from the pinned candidate; overlay exactly the seven fresh runtime files into app-data/backend-data. Verify every overlaid active-state checksum/metadata against frozen snapshot before candidate startup. Directory mounts are required for atomic writes; never replace candidate static registry with old static data. Fill a genuinely verified, short-lived `state-receipt.json` with source, owner authorization, frozen original, Pi/archive verification, snapshot hash map and paths; the deliberately expired BLOCKED receipt is not usable. Do not set flags as a substitute for work.
5. **Candidate verification:** use pinned Compose commands below, with no build/pull/recreate of unrelated services. Original must remain stopped. Before routing public traffic verify candidate source/release, state seeded/preserved, actual production-auth negative/positive checks server-side without emitting credentials, private route boundaries, loopback18091, six domain/source/record availability versus accepted baseline, and preserved truthful partial/503 classifications. Existing proxy helper has a strict HTTP200/ready=true target gate; if it refuses, stop—do not weaken/bypass it to reinterpret a503. A truthful503 is not automatically a product failure under owner instruction, but its acceptance cannot be substituted for this stricter tool prerequisite without reviewed resolution.
6. **Guarded cutover:** authorized administrator runs the deploy `sudo` command only after prior checks pass and current immutable snapshot/receipt binds those checks. Record returned `proxy_after_sha256` in receipt for inverse. No PR merge.
7. **Post-cutover acceptance:** public app200; API process/readiness; authenticated workflows and negatives; all six domain/source/record states; no new degradation; active data intact; actual Caddy routing; unchanged unrelated-service IDs/images/start times. Record timestamps, images, hashes and results. No unconditional success on basic health alone.
8. **Abort/rollback:** before candidate ever starts and before proxy change, restore untouched original (`docker update --restart=unless-stopped sc-site-intelligence` then `docker start sc-site-intelligence`) and verify pre-window operation. Once candidate has started, assume it may have written: drain candidate, preserve latest shared active state, launch pinned OLD IMAGE against SAME ACTIVE DIRECTORIES, verify health/auth/state. If switch happened, run inverse `sudo` operation. If switch did not happen, API already targets8091: start shared-state rollback service on8091 and do NOT call inverse for a nonexistent switch. Never restart stale original layer over newer active writes. Any unexpected unrelated-service impact, missing state or failed verification stops promotion and invokes appropriate rollback.

## Exact candidate and rollback launch commands from RELEASE-REPORT.md

These require a real fresh snapshot, seeded active paths, current receipt and verified frozen writer state. They are **not runnable now** because RISK-01 is open. Docker operations use the existing authorized account; do not introduce additional sudo or blanket privilege grants.

```bash
cd /home/catalystadmin/si-2.1.4-release
export SI214_IMAGE=sha256:69591b22b5d0a3514ee4c0922f5518cc8031b65734f0d6e969e96519c4f667eb
export SI214_STATE=/home/catalystadmin/si-2.1.4-release/state/active
python3 guarded_proxy_switch.py --plan deployment-plan.json --receipt state-receipt.json --direction deploy --check-state-only &&
 docker compose -p site-intelligence-si214 -f production.compose.yml up -d --no-deps --no-build --wait --wait-timeout 120 site-intelligence-si214
# Stop at candidate-verification checkpoint above, then administrator switch.
```

Candidate drain after deployment authorization, if rollback becomes necessary:

```bash
docker update --restart=no sc-site-intelligence-si214
docker exec -i sc-site-intelligence-si214 python - --execute --approved-window SI214-EXISTING-OWNER-DEPLOYMENT-AUTHORIZATION < quiesce_uvicorn.py
# Bounded wait + clean-shutdown marker required; never force-kill to meet a deadline.
```

Rollback launch (same exported variables; candidate already quiescent, original stopped):

```bash
python3 guarded_proxy_switch.py --plan deployment-plan.json --receipt state-receipt.json --direction rollback --check-state-only &&
 docker compose -p site-intelligence-si214 -f production.compose.yml up -d --no-deps --no-build --wait --wait-timeout 120 site-intelligence-si214-rollback
# Verify old-image/shared-state operation, then inverse sudo switch ONLY if cutover occurred.
```

Failure to regain prior operational state is BLOCKED and requires immediate owner incident notification; never report DEPLOYED AND VERIFIED. Preserve logs/receipts without passwords or record bodies. No broad test rerun, new numbered release or image rebuild belongs to this handoff.
