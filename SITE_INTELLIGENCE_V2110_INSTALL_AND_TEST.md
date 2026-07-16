# Site Intelligence v2.11.0 Installation and Test Guide

Run the supplied installer from `~/Downloads`. It verifies the repository manifest, creates a safety backup, resets to `origin/main`, installs v2.11.0, runs the full regression and syntax suite, scans for secrets, packages repository and WordPress archives, commits, rebases, and pushes.

After Render deploys, confirm `/health` reports `2.11.0`, open `/app/?view=integration`, inspect `/api/public/v1/catalog`, and generate an embed manifest.
