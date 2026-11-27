# SI-2.1.4 — Corrected candidate administrator execution sheet

2026-10-30. **Technical recovery gate PASS; execution BLOCKED awaiting administrator availability.** Existing owner SI-only authorization retained; no renewed approval required. No passwords in chat/logs/files/GitHub. No unrestricted sudo grant or Docker-based host permission bypass.

Source `01ea3645617b38857f1316495f7dd0c77054a73d`. Backend `sha256:13290390307cf61e07217c942eabb649626a6127387ba781443726b6dae2ad5d`. Frontend `sha256:13ba5b9fed664562765058da0e5ad1c20cf85fa3e3f6ec20faa42616709fcc43`. Old backend89195c76 and original frontend3fd9e3aa retained. Full digests/rollback in RELEASE-REPORT.md. All other services untouched.

Administrator logs into Contabo (`vmi3544820`,94.72.113.77) in their OWN terminal. Their interactive authentication is performed locally with `sudo -v` before any writer pause; agent never receives password. Administrator must stay available for switch and inverse. Current audit-account noninteractive sudo is unavailable. Do not pause SI while waiting for this prerequisite.

Sequence: (1) verify pinned images/source/config/Caddy/protected services; (2) fresh graceful SI-only drain, frozen seven-file capture and Pi SHA/metadata verification; (3) new protected active dirs seeded with corrected static reference files and exactly seven latest runtime overlays, checksum verification; (4) current short-lived receipt bound to actual capture/approval and existing compatible restore proof; (5) corrected backend18091/frontend18096 start from pinned images only; missing/invalid/valid existing-token checks without emitting credentials, state and six truthful domain checks, original auth/config comparison; (6) administrator guarded dual SI-route switch; (7) public/auth/domain/source/record/state/service acceptance; (8) state-preserving rollback on any failure. Original frontend8096 stays running throughout.

Working directory `/home/catalystadmin/si-2.1.4-release/correction-01ea3645`. Exact start/env/check-state commands are in RELEASE-REPORT.md. The only privileged deployment operations are:

```bash
# Interactive authentication in administrator's own Contabo terminal, before maintenance:
sudo -v
# ONLY after candidate verification and real fresh receipt:
sudo python3 guarded_proxy_switch.py --plan corrected-deployment-plan.json --receipt corrected-state-receipt.json --direction deploy --execute
# ONLY after rollback candidate drain, latest shared-state old-image launch and checks:
sudo python3 guarded_proxy_switch.py --plan corrected-deployment-plan.json --receipt corrected-state-receipt.json --direction rollback --execute
```

Helper validates Caddy, atomically updates only SI API8091↔18091 and SI frontend8096↔18096, preserves metadata and runs `systemctl reload caddy`. Do not run unguarded edits/reloads or restore an old whole Caddyfile over other services. On its reload failure helper reverses only its own unchanged bytes. No system/package/nginx upgrade, auth reset or unrelated restart.

Before any candidate writes: abort restores original SI `unless-stopped` and starts original image/container. After candidate may have written: quiesce candidate (no force kill), retain latest shared active dirs, launch pinned old backend with those dirs, verify, then inverse Caddy if and only if switch occurred. Original frontend always provides8096 rollback target. Never start original stale backend layer over new writes. Keep snapshots and original containers intact.

Historical355 failures remain disclosed; zero new IDs verified. RISK-01 now closed by10 permanent behavior tests,6 actual browser cases and exact-image asset verification; no broader security certification. Candidate strict ready200 gate remains; do not weaken it to force a truthful503 through the tool. Stop on new degradation, auth failure, lost/mismatched state, config drift or unrelated service impact. No PR merge.
