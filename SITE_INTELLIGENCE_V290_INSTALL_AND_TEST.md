# Site Intelligence v2.9.0 Installation and Test Guide

Run the supplied installer from `~/Downloads`. It verifies the repository archive, resets the local repository to `origin/main`, applies v2.9.0, creates an isolated test environment when necessary, runs the complete regression suite and syntax checks, scans for secrets, builds the repository and WordPress ZIPs, commits, rebases, and pushes. After Render redeploys, confirm `/health` reports `2.9.0` and test `/app/?view=scenarios`.
