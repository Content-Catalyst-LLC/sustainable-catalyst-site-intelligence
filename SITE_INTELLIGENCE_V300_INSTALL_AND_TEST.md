# Install and Test Site Intelligence v3.0.0

1. Place the repository ZIP and installer in `~/Downloads`.
2. Run the installer commands supplied in `SITE_INTELLIGENCE_V300_TERMINAL_COMMANDS.txt`.
3. The installer creates a safety archive and backup branch, installs the release overlay, verifies the immutable manifest, builds an isolated Python environment, runs the full regression suite, validates Python, JavaScript, PHP, JSON, HTML IDs, and packages the WordPress plugin.
4. The installer uses authenticated GitHub CLI or SSH credentials and disables interactive Git username prompts.
5. After the push, deploy the latest `main` commit in Render with **Clear build cache & deploy**.
6. Confirm `/health`, `/release`, and `/public/build-info` report `3.0.0`.
7. Confirm `/public/connected-intelligence` and `/public/connected-intelligence/search?q=NASA` respond.
8. Install the v3.0.0 WordPress plugin only after backend parity is confirmed.

Public search is account-free. Private runtime records, credentials, and administrative history are not part of the connected public index.
