# Site Intelligence v2.10.0 Installation and Test Guide

Run the supplied installer from `~/Downloads`. It verifies the repository archive and SHA-256 manifest, creates a safety backup, resets the local repository to `origin/main`, installs v2.10.0, creates an isolated Python test environment when needed, runs the complete regression suite and syntax checks, scans for secrets, builds repository and WordPress ZIPs, commits, rebases, and pushes.

After Render redeploys, confirm `/health` reports `2.10.0` and test `/app/?view=research`. Create an investigation, add notes and evidence, capture a public view, save locally, export JSON, generate a briefing packet, and create a structured handoff.

The workspace uses browser-local storage. Export important investigations before clearing browser storage.
