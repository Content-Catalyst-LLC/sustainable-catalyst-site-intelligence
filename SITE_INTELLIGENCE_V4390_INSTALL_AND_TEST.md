# Install and Test Site Intelligence v4.39.0

## 1. Push the repository release

Run `SITE_INTELLIGENCE_V4390_TERMINAL_COMMANDS.txt` on the Mac. The installer validates the release bundle, requires a clean Git checkout, applies the certified repository tree, commits, tags, and pushes it.

## 2. Deploy the backend on Contabo

Update the existing Site Intelligence service from GitHub using the deployment method already configured for the VPS. Confirm these URLs return version `4.39.0`:

```text
/health
/public/build-info
/v1/public/site-intelligence/summary
```

The summary must report schema `sc-site-intelligence-home-summary/1.0`.

## 3. Update WordPress

Upload and activate:

```text
sustainable-catalyst-site-intelligence-v4.39.0-wordpress-plugin.zip
```

The Installed Plugins screen must show version `4.39.0`.

## 4. Add the homepage module

Insert a WordPress Shortcode block where the Platform showcase should appear:

```text
[sc_site_intelligence_home]
```

## 5. Browser acceptance check

- The panel says `Site Intelligence Online` after loading.
- Four metric cells contain numeric backend-derived values.
- Current signals either render with sources or show the explicit no-current-signals state.
- Explore the World, Earth & Environment, Ocean & Space, and Open Site Intelligence navigate correctly.
- No iframe appears inside the homepage component.
- Mobile layout is single-column and does not overflow.
- With the backend temporarily unavailable, no metric is replaced by a made-up number.
