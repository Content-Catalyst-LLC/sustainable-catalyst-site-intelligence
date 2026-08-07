# Install and test Site Intelligence v3.25.0

1. Put the v3.25.0 installer and release bundle in `~/Downloads`.
2. Run the installer command supplied with the release.
3. Allow both deterministic validation passes to finish.
4. The promotion script pushes the exact validated Git tree, waits for Render, and verifies the live control-plane, country truth, record truth, browser, service-worker, and WordPress embed contracts.
5. Install the WordPress ZIP printed by the installer only after the live gate reports success.

## Public checks after deployment

- Open Data Truth and select **Control plane**.
- Confirm eight source rows appear.
- Confirm the selected country appears in Cross-workspace truth.
- Filter for World Bank and confirm one row remains.
- Export the control-plane JSON.
- Confirm the country selector and Record Truth controls still work.
