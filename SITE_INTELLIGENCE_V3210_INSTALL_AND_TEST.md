# Site Intelligence v3.22.0 — Install and Test

```bash
cd ~/Downloads
unzip -o sustainable-catalyst-site-intelligence-v3.22.0-release-bundle.zip
chmod +x install_and_push_site_intelligence_v3_21_0.sh
./install_and_push_site_intelligence_v3_21_0.sh
```

Run the complete backend suite during installation:

```bash
SC_SI_FULL_TESTS=1 ./install_and_push_site_intelligence_v3_21_0.sh
```

WordPress shortcode:

```text
[sc_live_intelligence_registry_collections]
```

The installer verifies the repository checksum and immutable manifest, runs the v3.22.0 release gate, validates Python/JSON/HTML/JavaScript/PHP assets, regenerates the WordPress ZIP, commits locally, and pushes only when push is enabled and the configured remote is reachable.
