# Site Intelligence v4.40.0.2 — Install and Test

## 1. Apply, validate, commit, tag, and push on macOS

```bash
cd ~/Downloads
rm -rf sc-site-v44002-patch
unzip -q sustainable-catalyst-site-intelligence-v4.40.0.2-tiny-patch.zip -d sc-site-v44002-patch
cd sc-site-v44002-patch
chmod +x apply_and_push_site_intelligence_v4_40_0_2_macos.sh
./apply_and_push_site_intelligence_v4_40_0_2_macos.sh \
  "$HOME/Downloads/sustainable-catalyst-site-intelligence"
```

Expected final line:

```text
PASS: Site Intelligence v4.40.0.2 committed, tagged, and pushed.
```

## 2. Deploy and verify the backend on Contabo

From macOS:

```bash
cd ~/Downloads
scp -i ~/.ssh/id_ed25519 \
  -o IdentitiesOnly=yes \
  sustainable-catalyst-site-intelligence-backend-v4.40.0.2.zip \
  upgrade_site_intelligence_backend_v4_40_0_2_contabo.sh \
  catalystadmin@94.72.113.77:/tmp/

ssh -i ~/.ssh/id_ed25519 \
  -o IdentitiesOnly=yes \
  catalystadmin@94.72.113.77
```

On Contabo:

```bash
chmod +x /tmp/upgrade_site_intelligence_backend_v4_40_0_2_contabo.sh
/tmp/upgrade_site_intelligence_backend_v4_40_0_2_contabo.sh
```

Do not install WordPress until the backend upgrader prints its final PASS. It validates the exact `172 / 14 / 35 / 8` metric contract and the governed homepage ticker feed locally and publicly.

## 3. Install WordPress only after backend PASS

Upload and replace the current plugin with:

```text
sustainable-catalyst-site-intelligence-v4.40.0.2-wordpress.zip
```

WordPress must report plugin version **4.40.0.2**.

Clear WordPress caches/transients, then hard refresh the homepage.

## 4. Browser acceptance

The Site Intelligence homepage widget must show:

```text
172  country profiles
14   enabled connectors
35   public workspaces
8    live ticker feeds
```

The current-signal count remains separate and may vary per refresh.

The Live Intelligence ticker must be visibly embedded inside the Site Intelligence widget, between the capability strip and the four current signal cards. On ordinary desktop motion settings it must scroll continuously. Hover, focus, manual pause, reduced-motion, and mobile behavior must remain intact.

Do not advance to a new feature release until browser acceptance passes.
