# Site Intelligence v4.13.0 — Install and Test

Place the v4.13.0 installer and release bundle in `~/Downloads`, then run the commands in `SITE_INTELLIGENCE_V41200_TERMINAL_COMMANDS.txt`.

The installer verifies bundle SHA-256 checksums, extracts the repository, installs Python dependencies in an isolated virtual environment, runs the deterministic v4.12 verifier twice, promotes the exact validated tree to GitHub/Render, and prints the WordPress plugin ZIP path only after the live gate succeeds.

The WordPress ZIP should be installed only after Terminal reports the exact **v4.13.0 GitHub and Render live gate passed**.
