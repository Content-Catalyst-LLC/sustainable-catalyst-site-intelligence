# v4.55.3.2.1 Install and Verify

Deploy **backend first**, then standalone web.

## Backend

Run `deploy/contabo/upgrade_site_intelligence_backend_v4_55_3_2_1_contabo.sh` with the v4.55.3.2.1 backend ZIP. The helper preserves dynamic production data, promotes 44 immutable release-bound files, rebuilds `sc-site-intelligence`, verifies the runtime/context contract, and accepts truthful degraded readiness.

After deployment verify `/health`, `/ready?country=KEN`, and `/public/capability-health?probe=true&country=KEN`.

## Web

Run `deploy/contabo/upgrade_site_intelligence_web_v4_55_3_2_1_contabo.sh` with the web ZIP. Port allocation remains `127.0.0.1:8096`. The helper uses temporary response files rather than `curl | grep -q`, avoiding the previous pipefail false failure.

Then open `/economics/KEN` in a browser. Kenya must be selected inside the Economics workspace. With the current empty Economics domain, the status must state that Platform Core is connected but no matching official economics records are published for Kenya. Site health must be **Degraded** rather than **Offline** when `/health` succeeds and optional diagnostics fail.
