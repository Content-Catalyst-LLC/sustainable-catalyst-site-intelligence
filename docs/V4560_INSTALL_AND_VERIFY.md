# v4.56.0 Install and Verify

Deploy **backend first** and **web second**.

After source application, run:

```bash
python3 scripts/validate_v4560_release.py
```

Then run the targeted pytest regression line and browser certification. Package the release only after those pass.

On Contabo, deploy the backend ZIP with `upgrade_site_intelligence_backend_v4_56_0_contabo.sh`, then deploy the web ZIP with `upgrade_site_intelligence_web_v4_56_0_contabo.sh`.

A domain-degraded `/ready` response may remain truthful and does not invalidate core runtime certification as long as `/health`, production-certification contracts, browser transport, deep links, and capability-health structure pass.
