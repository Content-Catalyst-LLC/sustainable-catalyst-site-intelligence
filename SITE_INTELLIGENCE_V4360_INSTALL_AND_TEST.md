# Site Intelligence v4.39.0 R1 — Install and Test

R1 keeps the application and WordPress semantic version at `4.39.0`; the `R1` suffix identifies the corrected release artifact and certification lineage.

## Release-bundle installation

Use the R1 outer release bundle and run:

```bash
cd ~/Downloads
BUNDLE="$(find . -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v4.39.0-R1-release-bundle*.zip' -print | sort | tail -1)"
[ -n "$BUNDLE" ] || { echo "ERROR: v4.39.0 R1 release bundle not found."; exit 1; }
rm -rf site-intelligence-v4.39.0-R1-release
mkdir -p site-intelligence-v4.39.0-R1-release
unzip -q "$BUNDLE" -d site-intelligence-v4.39.0-R1-release
cd site-intelligence-v4.39.0-R1-release
chmod +x deploy_and_validate_site_intelligence_v4_36_0_R1_macos.sh
./deploy_and_validate_site_intelligence_v4_36_0_R1_macos.sh
```

## R1 browser invariant

The browser certification must find Ocean **after** v4 navigation consolidation at:

```text
#primaryNavigation > .v4000-nav-featured [data-ocean-entry="hub"]
```

The control must be visible and must open `/app/?view=earth&oceanMode=hub` without depending on successful Earth imagery initialization.

## Expected invariants

- backend/plugin version `4.39.0`
- repair designation `R1`
- Ocean systems `11`
- Ocean groups `5`
- primary areas `6`
- canonical routes `35`
- Ocean route delta `0`
- full backend regression `1667/1667`
- desktop/mobile/iframe workspace routes `35/35`
