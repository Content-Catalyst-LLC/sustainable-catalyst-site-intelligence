# Site Intelligence v3.23.6.4 installation and test guide

## Required downloads

- `sustainable-catalyst-site-intelligence-v3.23.6.4-release-bundle.zip`
- `deploy_and_validate_site_intelligence_v3_23_3_macos.sh`

## Terminal deployment

```bash
cd ~/Downloads

INSTALLER="$(find . -maxdepth 1 -type f -name 'deploy_and_validate_site_intelligence_v3_23_3_macos*.sh' -print0 | xargs -0 ls -t | head -1)"
BUNDLE="$(find . -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v3.23.6.4-release-bundle*.zip' -print0 | xargs -0 ls -t | head -1)"

chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

Install the WordPress ZIP only after Terminal reports that v3.23.6.4 is live.

## Production browser checklist

1. Open Overview and confirm the map and evidence drawer still work.
2. Open **Data truth** in the top controls.
3. Confirm every source has a publisher, endpoint, license, geographic coverage, temporal coverage, and refresh policy.
4. Confirm sources with no successful production retrieval say **demonstration** or **unavailable**, never live.
5. Confirm a last-known-good fallback says **recently cached** and displays a stale marker.
6. Confirm annual and periodic values say **historical snapshot**.
7. Confirm research metadata says **context only**.
8. Confirm the Data truth panel does not appear outside the Site Intelligence iframe on the WordPress host page.
