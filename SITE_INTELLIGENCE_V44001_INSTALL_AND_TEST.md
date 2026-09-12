# Site Intelligence v4.40.0.1 — Install and Test

## 1. Apply and push the repository patch on macOS

Place the tiny patch ZIP in `~/Downloads`, then run:

```bash
cd ~/Downloads
rm -rf sc-site-v44001-patch
unzip -q sustainable-catalyst-site-intelligence-v4.40.0.1-tiny-patch.zip -d sc-site-v44001-patch
cd sc-site-v44001-patch
chmod +x apply_and_push_site_intelligence_v4_40_0_1_macos.sh
./apply_and_push_site_intelligence_v4_40_0_1_macos.sh \
  "$HOME/Downloads/sustainable-catalyst-site-intelligence"
```

The installer synchronizes `main`, applies only the v4.40.0.1 repair payload, validates syntax/contracts, commits the patch, tags `v4.40.0.1`, and pushes both branch and tag.

## 2. Deploy the backend on Contabo — do this before WordPress

From the Mac:

```bash
cd ~/Downloads
scp -i ~/.ssh/id_ed25519 \
  -o IdentitiesOnly=yes \
  sustainable-catalyst-site-intelligence-backend-v4.40.0.1.zip \
  upgrade_site_intelligence_backend_v4_40_0_1_contabo.sh \
  catalystadmin@94.72.113.77:/tmp/

ssh -i ~/.ssh/id_ed25519 \
  -o IdentitiesOnly=yes \
  catalystadmin@94.72.113.77
```

On the VPS:

```bash
chmod +x /tmp/upgrade_site_intelligence_backend_v4_40_0_1_contabo.sh
/tmp/upgrade_site_intelligence_backend_v4_40_0_1_contabo.sh
```

The upgrader backs up the current backend, overlays only release code and the explicit immutable registry/policy allowlist, rebuilds the existing Docker service, then verifies local health, release identity, runtime feed counts, and the homepage summary contract.

Required backend result before proceeding:

```text
health.version = 4.40.0.1
summary.version = 4.40.0.1
country_profiles = numeric
registered_sources = numeric
enabled_sources = numeric
current_signals = numeric
```

## 3. Install the WordPress plugin

Upload:

```text
sustainable-catalyst-site-intelligence-v4.40.0.1-wordpress.zip
```

Choose **Replace current with uploaded**. Confirm the plugin reports **4.40.0.1**.

## 4. Clear WordPress and Site Intelligence transient caches

On Bluehost:

```bash
cd /home1/pctrqumy/public_html
wp cache flush

PREFIX="$(wp db prefix)"
wp db query "
DELETE FROM ${PREFIX}options
WHERE option_name LIKE '_transient_scsi_%'
   OR option_name LIKE '_transient_timeout_scsi_%';
"
```

## 5. Verify the public contracts

```bash
curl -fsS https://site-intelligence-api.sustainablecatalyst.com/health | python3 -m json.tool

curl -fsS \
  https://site-intelligence-api.sustainablecatalyst.com/v1/public/site-intelligence/summary \
  | python3 -m json.tool

curl -fsS \
  https://site-intelligence-api.sustainablecatalyst.com/public/live-intelligence/status \
  | python3 -m json.tool

curl -fsS \
  https://sustainablecatalyst.com/wp-json/sc-site-intelligence/v1/homepage-summary \
  | python3 -m json.tool

curl -fsS \
  https://sustainablecatalyst.com/wp-json/sc-site-intelligence/v1/live-intelligence/status \
  | python3 -m json.tool
```

## 6. Browser acceptance

Hard-refresh the homepage and verify all of the following:

- Site Intelligence reports Online.
- Country profiles is numeric.
- Registered live feeds is numeric.
- Enabled by default is numeric.
- Current signals is numeric and matches the bounded homepage refresh.
- The Live Intelligence ticker starts moving automatically on normal desktop motion settings.
- The ticker loops without a blank gap or visible jump.
- Hover, keyboard focus, and the pause button pause motion; resume restores motion.
- Reduced-motion mode remains static/manual and does not autoplay.
- Signal links remain clickable and keyboard accessible.
- The current signal cards still render.
- Explore the World, Earth & Environment, and Ocean & Space remain unchanged.
- Browser source loads `sc-site-intelligence.js?ver=4.40.0.1` and `sc-site-intelligence.css?ver=4.40.0.1`.
- No JavaScript error appears in the browser console during initial load or a live refresh.

Do not advance to the next Site Intelligence build until backend and browser acceptance both pass.
