# Site Intelligence v3.22.0 — Install and Test

## Install and push

```bash
cd ~/Downloads
unzip -o sustainable-catalyst-site-intelligence-v3.22.0-release-bundle.zip
chmod +x install_and_push_site_intelligence_v3_20_0.sh
./install_and_push_site_intelligence_v3_20_0.sh
```

Run the complete test suite:

```bash
SC_SI_FULL_TESTS=1 ./install_and_push_site_intelligence_v3_20_0.sh
```

## WordPress

Upload and activate `sustainable-catalyst-site-intelligence-v3.22.0-wordpress.zip`, then place:

```text
[sc_live_intelligence_registry_discovery]
```

The surface displays approved public records only. Search queries are not stored and no visitor profiles are created.
