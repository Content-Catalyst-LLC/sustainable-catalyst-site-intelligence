# Site Intelligence v2.13.0 Installation and Test Guide

## Artifacts

- `sustainable-catalyst-site-intelligence-v2.13.0-repo.zip`
- `sustainable-catalyst-site-intelligence-v2.13.0-wordpress.zip`
- `install_and_push_site_intelligence_v2_13_0.sh`

## Automated installation

Place the repository ZIP and installer in `~/Downloads`:

```bash
cd ~/Downloads
chmod 700 install_and_push_site_intelligence_v2_13_0.sh
bash ./install_and_push_site_intelligence_v2_13_0.sh
```

The installer:

1. verifies the packaged immutable manifest;
2. clones or resets the GitHub repository safely;
3. creates a timestamped archive and backup branch;
4. installs the v2.13.0 overlay;
5. creates a Python 3.13/3.12 validation environment;
6. installs development test dependencies including HTTPX2;
7. redirects all writable connector and cache paths outside the repository;
8. runs 405 tests and release-contract checks;
9. runs Python, JavaScript, JSON, YAML, and PHP syntax checks;
10. re-verifies the immutable manifest after tests;
11. packages the WordPress plugin;
12. commits and pushes through authenticated GitHub CLI or SSH without an interactive username prompt.

## Render deployment

After the push, open the Render service and select:

`Manual Deploy → Clear build cache & deploy`

Verify:

```bash
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/health | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/release | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/connectors/operations | python3 -m json.tool
```

The backend version must report `2.13.0` before installing the v2.13.0 WordPress plugin.

## WordPress deployment

Upload `sustainable-catalyst-site-intelligence-v2.13.0-wordpress.zip`, replace the existing plugin, clear WordPress and Cloudflare caches, and confirm version parity.

Public shortcode:

```text
[sc_public_connector_operations]
```

Administrator-only shortcode:

```text
[sc_connector_operations_control_center]
```

## Optional runtime paths

On ephemeral hosts, set writable paths to `/tmp`:

```text
SC_SI_CONNECTOR_OPERATIONS_STATE_PATH=/tmp/scsi-connector-operations-state.json
SC_SI_CONNECTOR_OPERATIONS_HISTORY_PATH=/tmp/scsi-connector-operations-history.jsonl
SC_SI_CONNECTOR_OPERATIONS_QUARANTINE_PATH=/tmp/scsi-connector-operations-quarantine.jsonl
```

Durable storage can be introduced later without changing the public API contract.
