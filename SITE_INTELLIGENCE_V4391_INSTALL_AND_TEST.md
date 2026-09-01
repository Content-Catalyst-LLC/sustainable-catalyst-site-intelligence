# Site Intelligence v4.39.1 — Install and Test

## 1. Apply and push the repository release on macOS

Place the release bundle in `~/Downloads`, then run:

```bash
cd ~/Downloads
unzip -q sustainable-catalyst-site-intelligence-v4.39.1-release-bundle.zip -d sustainable-catalyst-site-intelligence-v4.39.1-release
cd sustainable-catalyst-site-intelligence-v4.39.1-release
chmod +x install_and_push_site_intelligence_v4_39_1_macos.sh
./install_and_push_site_intelligence_v4_39_1_macos.sh "$HOME/Downloads/sustainable-catalyst-site-intelligence"
```

The installer validates source files, verifies WordPress ZIP asset identity, applies the release to the Git checkout, commits, tags `v4.39.1`, and pushes the active branch plus tag to GitHub.

## 2. Deploy the backend from the v4.39.1 Git commit

Deploy the new commit to the existing Site Intelligence service on the Contabo VPS. Do not reintroduce Render hostnames. Preserve the production environment variables and API token already configured on the VPS.

Expected health identity:

```text
version: 4.39.1
release_id: site-intelligence-v4.39.1
```

## 3. Install the WordPress plugin

Upload:

```text
sustainable-catalyst-site-intelligence-v4.39.1-wordpress-plugin.zip
```

WordPress should report plugin version **4.39.1**.

## 4. Verify the public feed and WordPress proxy

```bash
curl -sS -w '\nHTTP_STATUS:%{http_code}\n' \
  'https://site-intelligence-api.sustainablecatalyst.com/public/live-intelligence/homepage?limit=8&channel=global'

curl -sS -w '\nHTTP_STATUS:%{http_code}\n' \
  'https://sustainablecatalyst.com/wp-json/sc-site-intelligence/v1/live-intelligence/homepage?limit=8&channel=global'
```

Both should return HTTP 200 with a bounded signal array.

## 5. Verify browser assets

```bash
curl -sS 'https://sustainablecatalyst.com/' | \
  grep -oE 'https?[^"'"'"']*sc-site-intelligence\.js[^"'"'"']*' | head
```

The asset URL should include `ver=4.39.1`.

## 6. Browser acceptance

Hard refresh the homepage and verify:

- the Live Intelligence label does not remain `Unavailable` when the REST feed is healthy;
- the ticker renders multiple current signals;
- ticker motion works on normal desktop motion settings;
- reduced-motion mode remains static/manual as configured;
- the Site Intelligence homepage summary shows four capability metrics and current signal cards;
- Ocean, Space, World, and Earth entry points still open correctly.
