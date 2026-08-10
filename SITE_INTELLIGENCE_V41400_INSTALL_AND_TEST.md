# Install and Test — Site Intelligence v4.15.0

Place the v4.15.0 macOS installer and release bundle in `~/Downloads`, then execute the commands in `SITE_INTELLIGENCE_V41400_TERMINAL_COMMANDS.txt`.

The installer verifies bundle checksums, creates an isolated Python environment, runs a full deterministic validation pass, reruns static/package validation against the post-test tree, promotes through the resume-safe GitHub/Render workflow, and verifies the live release gate at the exact pushed commit.

Do not install the WordPress plugin ZIP until the installer reports that the live v4.15.0 release gate is ready. A WordPress/backend version mismatch intentionally blocks the gate.
