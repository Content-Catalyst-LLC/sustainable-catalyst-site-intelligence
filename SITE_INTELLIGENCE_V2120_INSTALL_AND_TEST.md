# Site Intelligence v2.12.0 Installation and Test Guide

Run the supplied installer from `~/Downloads`. It verifies the repository manifest, creates a safety backup, resets the repository to `origin/main`, installs v2.12.0, prepares an isolated Python test environment, runs the complete regression and syntax suite, scans for secrets, packages repository and WordPress archives, commits, rebases, and pushes.

After Render deploys, confirm `/health` reports `2.12.0`, open `/app/?view=experience`, inspect `/public/offline-experience/diagnostics`, and confirm `/app/manifest.webmanifest`, `/app/service-worker.js`, and `/app/offline.html` load successfully.

Cached records can become stale. External tiles, imagery, fonts, and third-party libraries may still require a live network connection. The accessibility checklist is a public engineering target, not certification.
