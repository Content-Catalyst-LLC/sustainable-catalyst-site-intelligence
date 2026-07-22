# Site Intelligence v3.22.0 — Install and Test

## Standard installation

```bash
cd ~/Downloads
unzip -o sustainable-catalyst-site-intelligence-v3.22.0-release-bundle.zip
chmod +x install_and_push_site_intelligence_v3_19_0.sh
./install_and_push_site_intelligence_v3_19_0.sh
```

The installer validates the repository checksum and immutable manifest, runs the focused registry-governance integration gate, checks Python/JSON/JavaScript/PHP syntax, builds the WordPress ZIP, commits the release, and pushes only when push is enabled.

## Full regression

```bash
SC_SI_FULL_TESTS=1 ./install_and_push_site_intelligence_v3_19_0.sh
```

## WordPress shortcode

```text
[sc_live_intelligence_registry_governance]
```

## Writable state

The following runtime files must remain outside immutable release manifests:

- `backend/data/live_intelligence_registry_governance_v3190/challenges_v3190.jsonl`
- `backend/data/live_intelligence_registry_governance_v3190/appeals_v3190.jsonl`
- `backend/data/live_intelligence_registry_governance_v3190/events_v3190.jsonl`
