# Site Intelligence v4.40.0.3 — Install and Test

## 1. Apply and push GitHub from macOS

```bash
cd ~/Downloads
rm -rf sc-site-v44003-patch
unzip -q sustainable-catalyst-site-intelligence-v4.40.0.3-tiny-patch.zip -d sc-site-v44003-patch
cd sc-site-v44003-patch
chmod +x apply_and_push_site_intelligence_v4_40_0_3_macos.sh
./apply_and_push_site_intelligence_v4_40_0_3_macos.sh "$HOME/Downloads/sustainable-catalyst-site-intelligence"
```

Do not proceed until the installer reports that `main` and tag `v4.40.0.3` were pushed.

## 2. Deploy and verify the Contabo backend

```bash
cd ~/Downloads
scp -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes \
  sustainable-catalyst-site-intelligence-backend-v4.40.0.3.zip \
  upgrade_site_intelligence_backend_v4_40_0_3_contabo.sh \
  catalystadmin@94.72.113.77:/tmp/

ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes catalystadmin@94.72.113.77
```

On the VPS:

```bash
chmod +x /tmp/upgrade_site_intelligence_backend_v4_40_0_3_contabo.sh
/tmp/upgrade_site_intelligence_backend_v4_40_0_3_contabo.sh
```

Do not install WordPress until backend deployment and verification pass.

## 3. Install WordPress

Upload `sustainable-catalyst-site-intelligence-v4.40.0.3-wordpress.zip` and replace the current plugin.

Clear WordPress/plugin caches and hard refresh the homepage.

## 4. Browser acceptance

Verify:

- capability strip remains **172 / 14 / 35 / 8**;
- ticker is visible and continuously moving;
- desktop movement is slow enough to read comfortably rather than racing;
- hovering the ticker pauses it on pointer devices;
- keyboard focus pauses the ticker;
- manual pause/resume still works;
- reduced-motion mode does not auto-scroll;
- current signal cards, Earth/Environment, Ocean/Space, and CTA remain unchanged.

For browser diagnostics, inspect the `.scsi-live-intelligence` element. The runtime now publishes:

- `data-scsi-ticker-pixels-per-second`
- `data-scsi-ticker-duration-seconds`
- `data-scsi-ticker-travel-pixels`
