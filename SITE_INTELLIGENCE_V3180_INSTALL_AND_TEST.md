# Site Intelligence v3.22.0 Install and Test

## Install

```bash
cd ~/Downloads
unzip -o sustainable-catalyst-site-intelligence-v3.22.0-release-bundle.zip
chmod +x install_and_push_site_intelligence_v3_18_0.sh
./install_and_push_site_intelligence_v3_18_0.sh
```

The installer verifies the repository ZIP checksum and immutable manifest, overlays the repository, runs the focused preservation-registry integration gate, validates Python, JSON, JavaScript, HTML IDs, and PHP, rebuilds the WordPress plugin ZIP, commits the release, and pushes unless `SC_SI_SKIP_PUSH=1` is set.

## Full regression

```bash
SC_SI_FULL_TESTS=1 ./install_and_push_site_intelligence_v3_18_0.sh
```

## WordPress

Install `sustainable-catalyst-site-intelligence-v3.22.0-wordpress.zip`, then place:

```text
[sc_live_intelligence_preservation_registry]
```

## Public verification

- `GET /public/live-intelligence/preservation-registry/policy`
- `GET /public/live-intelligence/preservation-registry/status`
- `GET /public/live-intelligence/preservation-registry/institutions`
- `GET /public/live-intelligence/preservation-registry/attestations`
- `GET /public/live-intelligence/preservation-registry/exchanges/{exchange_id}/consensus`
