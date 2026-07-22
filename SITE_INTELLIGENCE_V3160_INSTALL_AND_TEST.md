# Site Intelligence v3.19.0 — Install and Test

## Standard installation

```bash
cd ~/Downloads
unzip -o sustainable-catalyst-site-intelligence-v3.19.0-release-bundle.zip
chmod +x install_and_push_site_intelligence_v3_16_0.sh
./install_and_push_site_intelligence_v3_16_0.sh
```

The standard installer runs the focused cross-version preservation and release-governance gate, verifies the immutable manifest, validates Python/JSON/HTML/JavaScript/PHP syntax, rebuilds the WordPress plugin ZIP, and creates a Git commit before pushing.

## Complete regression

```bash
SC_SI_FULL_TESTS=1 ./install_and_push_site_intelligence_v3_16_0.sh
```

## WordPress shortcode

```text
[sc_live_intelligence_archive_audits]
```

## Public verification routes

```text
GET /public/live-intelligence/archive-audits/policy
GET /public/live-intelligence/archive-audits/status
GET /public/live-intelligence/archive-audits
GET /public/live-intelligence/archive-audits/{audit_id}
GET /public/live-intelligence/archive-audits/custody
```

Site Intelligence does not run a scheduler, transfer records remotely, write to institutional systems, mutate archives, or delete records.
