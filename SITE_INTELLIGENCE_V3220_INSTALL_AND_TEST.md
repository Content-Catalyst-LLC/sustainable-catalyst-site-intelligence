# Site Intelligence v3.22.0 — Install and Test

1. Place the release bundle in `~/Downloads`.
2. Extract it.
3. Make `install_and_push_site_intelligence_v3_22_0.sh` executable.
4. Run the installer.

```bash
cd ~/Downloads
unzip -o sustainable-catalyst-site-intelligence-v3.22.0-release-bundle.zip
chmod +x install_and_push_site_intelligence_v3_22_0.sh
./install_and_push_site_intelligence_v3_22_0.sh
```

Set `SC_SI_FULL_TESTS=1` to run the complete repository test suite. The default installer gate runs the registry discovery, collection, and publication tests plus the v3.22.0 release contract.
