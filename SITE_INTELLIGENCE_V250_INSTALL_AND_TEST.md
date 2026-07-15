# Site Intelligence v2.5.0 installation and validation

Place these files in `~/Downloads`:

- `sustainable-catalyst-site-intelligence-v2.5.0.zip`
- `install_and_push_site_intelligence_v2_5_0.sh`

Run:

```bash
cd ~/Downloads
chmod 700 install_and_push_site_intelligence_v2_5_0.sh
bash ./install_and_push_site_intelligence_v2_5_0.sh
```

The installer creates a safety backup, resets the repository to `origin/main`, verifies the release manifest, creates an isolated Python test environment, runs the full regression suite, validates syntax and formats, scans for potential secrets, builds repository and WordPress ZIPs, commits, rebases, and pushes.

## Render variables

```text
SC_SI_PLATFORM_CORE_ENABLED=true
SC_SI_PLATFORM_CORE_URL=https://YOUR-CORE-SERVICE.onrender.com
SC_SI_PLATFORM_CORE_PUBLIC_API_KEY=<set securely in Render>
SC_SI_HUMANITARIAN_CONFLICT_DISPLACEMENT_ENABLED=true
SC_SI_HUMANITARIAN_CONFLICT_DISPLACEMENT_TIMEOUT_SECONDS=9
SC_SI_HUMANITARIAN_CONFLICT_DISPLACEMENT_CACHE_TTL_SECONDS=90
```

The workspace can still show existing non-fabricated Site Intelligence public events when Platform Core is not configured. It never substitutes demonstration crisis records.
