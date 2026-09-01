# Site Intelligence v4.39.0 R2

## Compact Capability Console

This revision retains the R1 visual identity while making the homepage component stand on its own, use less vertical space, and describe the platform more accurately.

### Homepage presentation

- Reduced console width, padding, header scale, image height, card height, and inter-section spacing.
- Retained the high-resolution Earth, Space, and Ocean triptych and original scrolling Live Intelligence ticker.
- Increased the homepage ticker request ceiling from 12 to 16 signals.
- Added a compact `Featured now` count above the bounded signal cards.
- A separate homepage v4.3.1 template removes the generic `cch-section cch-platform-feature` wrapper that produced the tan background.

### Capability truth model

- `172 country profiles` comes from the country identity registry.
- `14 enabled connectors` comes from the connector operations registry. Enabled does not mean every connector is real-time; credential and cache states remain explicit.
- `35 public workspaces` comes from the unified public intelligence policy across six primary areas.
- `8 live ticker feeds` comes from the narrower governed Live Intelligence source registry.
- The four homepage highlight cards remain a bounded selection and are no longer presented as the total platform capability.

### Deployment identity

Both the backend and WordPress plugin remain version `4.39.0`. The Git tag is `v4.39.0-r2`. Because the public summary contract now reports broader capability metrics, deploy the backend container and replace the WordPress plugin together.
