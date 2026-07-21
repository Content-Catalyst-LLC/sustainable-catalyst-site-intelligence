# Site Intelligence v3.13.0 — Install and Test

```bash
cd ~/Downloads
unzip -o sustainable-catalyst-site-intelligence-v3.13.0-release-bundle.zip
chmod +x install_and_push_site_intelligence_v3_13_0.sh
./install_and_push_site_intelligence_v3_13_0.sh
```

To rerun the complete validated backend suite during installation:

```bash
SC_SI_FULL_TESTS=1 ./install_and_push_site_intelligence_v3_13_0.sh
```

After the backend and WordPress plugin are deployed, place the public governance surface where appropriate:

```text
[sc_live_intelligence_release_operations]
```

Verify:

- `/public/live-intelligence/release-operations/policy`
- `/public/live-intelligence/release-operations/status`
- `/public/live-intelligence/release-operations/corrections`

The public surface is read-only. Deployment receipts, verification, issues, corrections, rollbacks, approvals, and handoff receipts use protected administrative routes.
