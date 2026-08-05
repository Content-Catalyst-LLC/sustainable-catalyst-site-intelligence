# Site Intelligence v3.23.2 installation and test guide

## Required downloads

- `sustainable-catalyst-site-intelligence-v3.23.2-release-bundle.zip`
- `deploy_and_validate_site_intelligence_v3_23_2_macos.sh`

## Terminal deployment

```bash
cd ~/Downloads

INSTALLER="$(find . -maxdepth 1 -type f \
  -name 'deploy_and_validate_site_intelligence_v3_23_2_macos*.sh' \
  -print0 | xargs -0 ls -t | head -1)"

BUNDLE="$(find . -maxdepth 1 -type f \
  -name 'sustainable-catalyst-site-intelligence-v3.23.2-release-bundle*.zip' \
  -print0 | xargs -0 ls -t | head -1)"

chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

The installer validates twice, synchronizes the GitHub branch, waits for Render, verifies the live map interaction contract and assets, and then prints the verified WordPress ZIP path.

## WordPress installation

Install the WordPress ZIP only after Terminal reports that v3.23.2 is live. Replace the current plugin, purge WordPress and CDN caches, and open the page in a new Incognito window.

## Production browser checklist

1. Open Overview and confirm the map has non-zero dimensions and visible local geography.
2. Open **Layers & filters**.
3. Change imagery opacity and confirm the satellite layer changes without removing vector context.
4. Filter to one semantic category and confirm the record count, list, and map update together.
5. Select an event list row and confirm the map focuses the same record.
6. Enable clustering at global zoom and confirm grouped counts appear.
7. Use **Fit results** and confirm the map frames the filtered records.
8. Copy the map link, open it in another tab, and confirm filters, center, zoom, imagery, and selected record restore.
9. Confirm the WordPress host page does not show the production-truth banner outside the iframe.
10. Confirm Site Health reports the active visible map rather than hidden surfaces.
