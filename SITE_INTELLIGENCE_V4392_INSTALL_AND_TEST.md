# Install and Test Site Intelligence v4.39.2

## 1. Apply and push the repository release on macOS

Use `install_and_push_site_intelligence_v4_39_2_macos.sh` from the release bundle. The installer requires a clean Git checkout and applies only the certified changed/runtime metadata files plus v4.39.2 validation artifacts. It does not replace or delete the rest of the repository.

## 2. Deploy the backend on Contabo

Deploy the Git commit containing v4.39.2 and restart the existing Site Intelligence backend service using the same Contabo deployment method already in use.

Confirm:

```text
https://site-intelligence-api.sustainablecatalyst.com/health
https://site-intelligence-api.sustainablecatalyst.com/public/build-info
```

Both must report `4.39.2`, and build info must expect WordPress plugin `4.39.2`.

## 3. Update WordPress

Upload:

```text
sustainable-catalyst-site-intelligence-v4.39.2-wordpress-plugin.zip
```

Choose **Replace current with uploaded**. The plugin screen must report `4.39.2`.

## 4. Clear cache

Run on Bluehost:

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

Then hard-refresh the homepage.

## 5. Acceptance check

- Site Intelligence presentation remains the approved v4.39.0 design.
- Earth / Space / Ocean triptych remains present on the WordPress homepage.
- Explore the World, Earth & Environment, and Ocean & Space links remain present.
- Live Intelligence renders current returned signals and scrolls/rotates normally.
- A renderer exception does not replace a successfully returned feed with `LIVE INTELLIGENCE TEMPORARILY UNAVAILABLE`.
- Genuine REST/proxy failure still produces the explicit unavailable state.
- Browser source shows `sc-site-intelligence.js?ver=4.39.2`.
- WordPress and backend both report `4.39.2` and the release gate is matched.
