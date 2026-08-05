# Install and test Site Intelligence v3.23.2

## Required files

- `sustainable-catalyst-site-intelligence-v3.23.2-release-bundle.zip`
- `deploy_and_validate_site_intelligence_v3_23_1_macos.sh`

Place both files in `~/Downloads`.

## Terminal deployment

```bash
cd ~/Downloads

INSTALLER="$(find . -maxdepth 1 -type f \
  -name 'deploy_and_validate_site_intelligence_v3_23_1_macos*.sh' \
  -print0 | xargs -0 ls -t | head -1)"

BUNDLE="$(find . -maxdepth 1 -type f \
  -name 'sustainable-catalyst-site-intelligence-v3.23.2-release-bundle*.zip' \
  -print0 | xargs -0 ls -t | head -1)"

chmod +x "$INSTALLER"
bash "$INSTALLER" "$BUNDLE"
```

The installer validates the package twice, promotes the exact Git tree, waits for Render, verifies `/public/workspaces/production-truth`, and prints the WordPress ZIP only after the live gate is ready.

## WordPress installation

After Terminal reports success, upload the printed ZIP through:

**WordPress → Plugins → Add New → Upload Plugin**

Replace the current plugin and purge WordPress, hosting, CDN, service-worker, and browser caches.

## Production browser checklist

1. Open every navigation route once.
2. Confirm the production-state bar reports ready, empty, degraded, or unavailable rather than remaining on an indefinite loading state.
3. Confirm no enabled route opens a blank workspace.
4. Copy a deep link, reload it, and verify the same workspace opens.
5. Use browser Back and Forward and verify the active route changes correctly.
6. Temporarily block one public endpoint and verify the active route reports degraded while other routes remain usable.
7. Restore the endpoint and verify the active route returns to ready without a full application reload.
8. Confirm a route with no matching records displays its route-specific empty state.
9. Confirm Site Health and the production-state bar do not claim upstream sources were checked when only local contracts were verified.
