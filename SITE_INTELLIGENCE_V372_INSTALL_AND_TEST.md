# Site Intelligence v3.8.0 Install and Test

1. Place the v3.8.0 release bundle in `~/Downloads` and unzip it.
2. Run `chmod +x install_and_push_site_intelligence_v3_7_2.sh`.
3. Run `./install_and_push_site_intelligence_v3_7_2.sh`.
4. Deploy the updated backend from the repository and install the v3.8.0 WordPress ZIP.
5. Confirm `/public/build-info` and the WordPress plugin both report `3.8.0`.
6. Confirm the homepage ticker loads and `/public/live-intelligence/analytics-policy` reports aggregate-only measurement.
7. Open one signal and verify the aggregate summary increments without recording a visitor identifier, page path, URL, referrer, or user agent.

Runtime analytics state defaults to `backend/data/live_intelligence_analytics_state_v372.json`. On Render, point `SC_SI_LIVE_INTELLIGENCE_ANALYTICS_STATE_PATH` to persistent storage when cross-deploy retention is desired. The state file is runtime data and is excluded from release manifests and Git commits.
