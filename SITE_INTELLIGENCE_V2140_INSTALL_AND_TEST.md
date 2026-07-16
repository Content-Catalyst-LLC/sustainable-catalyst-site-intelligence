# Site Intelligence v2.14.0 Installation and Test Guide

## Artifacts

- `sustainable-catalyst-site-intelligence-v2.14.0-repo.zip`
- `sustainable-catalyst-site-intelligence-v2.14.0-wordpress.zip`
- `install_and_push_site_intelligence_v2_14_0.sh`

## Automated installation

Place the repository ZIP and installer in `~/Downloads`:

```bash
cd ~/Downloads
chmod 700 install_and_push_site_intelligence_v2_14_0.sh
bash ./install_and_push_site_intelligence_v2_14_0.sh
```

The installer:

1. verifies the packaged immutable manifest;
2. clones or safely resets the GitHub repository;
3. creates a timestamped archive and backup branch;
4. installs the v2.14.0 overlay;
5. creates an isolated Python 3.13/3.12/3.11 validation environment;
6. installs development dependencies and explicitly verifies HTTPX2/TestClient compatibility;
7. redirects all writable archive, connector, cache, and queue paths outside the repository;
8. runs 417 tests and the v2.14.0 release contract;
9. runs Python, JavaScript, JSON, YAML, webmanifest, and PHP syntax checks;
10. re-verifies the immutable manifest after testing;
11. packages the WordPress plugin;
12. commits and pushes through authenticated GitHub CLI or SSH without an interactive username prompt.

## Render deployment

After the GitHub push, open the Render service and select:

`Manual Deploy → Clear build cache & deploy`

Verify the backend before installing the WordPress plugin:

```bash
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/health | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/release | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/history | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/history/datasets | python3 -m json.tool
```

The backend must report `2.14.0` before the v2.14.0 WordPress plugin is installed.

## WordPress deployment

Upload `sustainable-catalyst-site-intelligence-v2.14.0-wordpress.zip`, replace the existing plugin, clear WordPress and Cloudflare caches, and confirm version parity.

Public shortcode:

```text
[sc_public_temporal_intelligence]
```

Administrator-only shortcode:

```text
[sc_historical_archive_control_center]
```

## Historical archive storage

The default file-backed path is:

```text
backend/data/historical_archive_v2140/
```

That path is deliberately excluded from Git and the release manifest. On an ephemeral Render filesystem, use `/tmp` only for non-durable evaluation. For history that must survive redeployments, attach a persistent disk and set the archive paths to its mount location.

Example durable configuration, assuming a disk mounted at `/var/data`:

```text
SC_SI_HISTORICAL_ARCHIVE_ROOT_PATH=/var/data/site-intelligence/history
SC_SI_HISTORICAL_ARCHIVE_INDEX_PATH=/var/data/site-intelligence/history/snapshot_index_v2140.jsonl
SC_SI_HISTORICAL_ARCHIVE_CHANGE_PATH=/var/data/site-intelligence/history/change_events_v2140.jsonl
SC_SI_HISTORICAL_ARCHIVE_REVISION_PATH=/var/data/site-intelligence/history/revision_events_v2140.jsonl
SC_SI_HISTORICAL_ARCHIVE_RETENTION_LOG_PATH=/var/data/site-intelligence/history/retention_events_v2140.jsonl
```

## Command-line inspection

```bash
cd ~/sustainable-catalyst-site-intelligence
python3 scripts/historical_archive_v2140.py datasets
python3 scripts/historical_archive_v2140.py snapshots --dataset climate-energy-timeseries
python3 scripts/historical_archive_v2140.py retention --days 3650 --max-snapshots 3650
```

Retention is dry-run by default. The `--apply` flag is required before deletion occurs.
