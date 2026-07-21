# Site Intelligence v3.12.0 — Install and Test

1. Unzip the release bundle in Downloads.
2. Make `install_and_push_site_intelligence_v3_12_0.sh` executable.
3. Run it from Terminal.
4. Deploy the backend after the repository push.
5. Install the generated WordPress ZIP and verify the backend/plugin versions match.
6. Add `[sc_live_intelligence_publication_releases]` to a governance page.

The installer verifies the immutable manifest, runs the full test suite and release contracts, checks Python/JSON/JavaScript/PHP syntax, builds the WordPress ZIP, commits locally, and pushes only when `SC_SI_NO_PUSH` is not set.
