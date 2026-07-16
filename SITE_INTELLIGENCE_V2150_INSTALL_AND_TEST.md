# Site Intelligence v2.15.0 Installation and Test Guide

## Artifacts

- `sustainable-catalyst-site-intelligence-v2.15.0-repo.zip`
- `sustainable-catalyst-site-intelligence-v2.15.0-wordpress.zip`
- `install_and_push_site_intelligence_v2_15_0.sh`

## Automated installation

Place the repository ZIP and installer directly in `~/Downloads`:

```bash
cd ~/Downloads
chmod 700 install_and_push_site_intelligence_v2_15_0.sh
bash ./install_and_push_site_intelligence_v2_15_0.sh
```

The installer:

1. verifies the packaged immutable manifest;
2. clones or safely resets the GitHub repository;
3. creates a timestamped safety archive and backup branch;
4. installs the v2.15.0 overlay;
5. creates an isolated Python 3.13/3.12/3.11 validation environment;
6. installs development dependencies and explicitly verifies HTTPX2/TestClient compatibility;
7. redirects connector, historical archive, spatial evidence, country cache, and queue state outside the repository;
8. runs 430 backend tests and the v2.15.0 release contract;
9. runs Python, JavaScript, service-worker, JSON, webmanifest, YAML, and PHP checks;
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
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/spatial | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/spatial/layers | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/spatial/methodology | python3 -m json.tool
```

The backend must report `2.15.0` before the v2.15.0 WordPress plugin is installed.

## WordPress deployment

Upload `sustainable-catalyst-site-intelligence-v2.15.0-wordpress.zip`, replace the existing plugin, clear WordPress and Cloudflare caches, and confirm version parity.

Public shortcode:

```text
[sc_public_spatial_evidence]
```

Administrator-only shortcode:

```text
[sc_spatial_evidence_control_center]
```

The standalone public workspace is:

```text
/app/?view=spatial
```

## Spatial evidence storage

The default writable path is:

```text
backend/data/spatial_evidence_v2150/
```

That path is deliberately excluded from Git and the immutable release manifest. On an ephemeral Render filesystem, use `/tmp` only for evaluation. For areas, datasets, versions, and analyses that must survive redeployment, attach a persistent disk and configure the paths below.

Example durable configuration for a disk mounted at `/var/data`:

```text
SC_SI_SPATIAL_EVIDENCE_ROOT_PATH=/var/data/site-intelligence/spatial
SC_SI_SPATIAL_EVIDENCE_AREAS_PATH=/var/data/site-intelligence/spatial/areas_v2150.jsonl
SC_SI_SPATIAL_EVIDENCE_DATASETS_PATH=/var/data/site-intelligence/spatial/datasets_v2150.jsonl
SC_SI_SPATIAL_EVIDENCE_ANALYSIS_PATH=/var/data/site-intelligence/spatial/analyses_v2150.jsonl
```

The policy and layer catalog remain immutable release files and should continue using their packaged default paths.

## Historical archive storage

v2.14.0 historical state remains separately configurable. A durable deployment should preserve both historical and spatial paths on the persistent disk.

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
python3 scripts/spatial_evidence_v2150.py summary
python3 scripts/spatial_evidence_v2150.py layers
python3 scripts/spatial_evidence_v2150.py areas --public
python3 scripts/spatial_evidence_v2150.py datasets --public
```

Create-area and dataset-registration commands accept JSON request files that use the same contracts as the administrator API.

## Interpretation boundaries

- Coordinates must be EPSG:4326 longitude and latitude.
- Non-point proximity is explicitly approximate.
- Missing metric values are never silently imputed.
- Spatial overlap or proximity does not establish causation or responsibility.
- The studio must not be used for military targeting or operational tracking of people.
