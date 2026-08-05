# Site Intelligence v3.22.1 — Install and Test

## Backend repository

1. Unzip the repository package.
2. Open Terminal in the extracted repository.
3. Run:

```bash
cd backend
PYTHONPATH=. python3 -m pytest -q
```

Expected result:

```text
847 passed
```

To run the public application locally:

```bash
cd backend
PYTHONPATH=. python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8091
```

Open `http://127.0.0.1:8091/app/`.

## WordPress plugin

1. In WordPress, go to **Plugins → Add New → Upload Plugin**.
2. Upload `sustainable-catalyst-site-intelligence-v3.22.1-wordpress-plugin.zip`.
3. Replace the existing plugin when WordPress prompts you.
4. Activate the plugin if it is not already active.
5. Purge WordPress, host, and browser caches.

## Map checks

- Open Overview, Live Events, Country, Compare, Earth Observation, Thematic Intelligence, and Spatial Evidence.
- Confirm maps render normally when public map services are available.
- In a network-restricted browser, confirm a static geographic grid appears instead of a blank or crashed map.
- Confirm Spatial Evidence displays a map even when no public area/dataset has yet been published.
- Confirm the interface labels contextual locations separately from matched evidence.

## Embed checks

When public embeds are enabled, `/app/` should send a `frame-ancestors` Content Security Policy and should not send `X-Frame-Options: SAMEORIGIN`.

When public embeds are disabled, `/app/` should send both:

```text
Content-Security-Policy: frame-ancestors 'self'
X-Frame-Options: SAMEORIGIN
```
