# v4.56.0 Install and Verify

Site Intelligence v4.56.0 is the standalone production consolidation and certification boundary. Deploy backend first, then web. Run `python3 scripts/validate_v4560_release.py`, the targeted pytest regression line, and `python3 scripts/browser_certify_v4560.py` before production deployment. A domain-degraded `/ready` response may truthfully be 503; `/health` remains the core liveness authority and no release step may fabricate domain readiness.
