# Site Intelligence v4.66.0 — Ocean Image & Observation Explorer

**Status:** locally tested source overlay, awaiting Contabo deployment and browser certification. Source reconciliation remains open in PR #2.

This release is an **additive frontend-only** Ocean Image & Observation Explorer. It adds an eighth tab to show NASA GIBS browse imagery next to explicitly dated NOAA ocean evidence. The five evidence sources are SST, chlorophyll, salinity, geostrophic currents, and sea-level anomaly. Wave forecasts remain in their own sixth tab.

The viewer does **not** independently establish temporal synchrony, NASA acquisition timestamp, pixel-to-cell registration, analytical fusion, satellite radiometric validity, or accuracy of third-party inputs. The downloadable JSON describes image URL, requested layer/date/extent, ocean query URL, sourced summary/receipt if available, and limitations. It does not contain satellite pixels or an invented digest.

Local package tests: 7/7 PASS including JavaScript syntax and idempotent installer verification.

Production install is explicitly blocked on review of the full release ZIP, safety of deployment source, and browser certification. No backend main.py replacement or rebuild.

### GitHub reconciliation

The uploaded Contabo source archive was collected before v4.65.0 and does not contain the NASA v4.65.0 assets. **The synchronized repository source is not yet complete.** Code modules must be imported and compared against the existing repo before the PR is merged. This documentation commit does not imply the v4.66.0 code has been pushed.