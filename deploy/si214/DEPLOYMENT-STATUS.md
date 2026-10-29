# SI-2.1.4 — Controlled deployment attempt

**BLOCKED before production mutation.** Owner deployment authorization and conditional historical-test exception are recorded. Do not request that authorization again.

Pinned AMD64 candidate `sha256:69591b22b5d0a3514ee4c0922f5518cc8031b65734f0d6e969e96519c4f667eb`, source `7a15666cdd1f8152272f74dd69427d810a215e3d`, and old image `sha256:89195c76cf1788b98b59b1fad669cd2c507f1d8459b9b2f967782a6cb918c207` verified on vmi3544820. Original SI ID/image/running state and baseline Caddy hash verified unchanged.

The preflight command `sudo -n -l` returned `sudo: a password is required`. The guarded switch requires root and the audit account cannot execute it unattended. No attempt was made to bypass host permissions using Docker. No writer was paused, fresh state copied, candidate started, Caddy changed or unrelated service operated in this attempt. Earlier certified recovery assets remain intact.

Resume with an authorized Contabo administrator available for both switch and inverse rollback. At the coordinated cutover checkpoint, AFTER fresh frozen snapshot/Pi verification, state seeding, candidate readiness/authentication/integrity and routing checks and a genuine current deployment receipt, the reviewed administrator operation is:

```bash
cd /home/catalystadmin/si-2.1.4-release
sudo python3 guarded_proxy_switch.py --plan deployment-plan.json --receipt state-receipt.json --direction deploy --execute
```

This command is not ready to run now. The blocked receipt deliberately remains expired; do not substitute the earlier recovery-only receipt. Existing RELEASE-REPORT.md contains the pinned start and shared-state rollback sequence. Do not grant unrestricted passwordless sudo or transmit passwords through chat. An administrator may execute the reviewed commands interactively at the coordinated checkpoints.

The historical exception is conditional. Zero new failing IDs remains verified by prior comparison; the suite is not green. A message-based triage of the 356 retained failures identified diagnostic/packaging and bridge exceptions that still require contextual assessment before certifying no critical security, authentication, integrity or recovery defect among them. This triage is not proof of a critical defect and is not a completed exception-safety assessment. No broad tests were repeated.

Final result: **BLOCKED**, not deployed and not rolled back (no cutover occurred).
