# Site Intelligence v3.23.6.4 installation

1. Download the release bundle and macOS installer into Downloads.
2. Run the Terminal block provided with the release.
3. The installer verifies bundle checksums, creates an isolated Python environment, runs all tests twice, and executes the mandatory complete-shell browser gate.
4. The installer promotes the exact Git tree and waits for the Render release gate.
5. Install the printed WordPress ZIP only after the success message.

Google Chrome, Chromium, Microsoft Edge, or Brave must be installed. Browser validation is intentionally not skippable for this emergency release.
