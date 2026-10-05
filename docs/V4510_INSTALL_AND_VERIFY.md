# Site Intelligence v4.51.0 Install & Verify

Run `scripts/validate_v4510_release.py`, then execute the current-contract pytest suite covering v4.46-v4.51 plus release reconciliation and energy consumers. Expected result: **113 passed**.

Production deployment uses `deploy/contabo/upgrade_site_intelligence_backend_v4_51_0_contabo.sh`. The installer preserves dynamic `backend/data` content, then explicitly promotes 33 certified release-bound registries/policies, including `spatial_research_handoff_registry_v4510.json`.

After deployment verify `/health`, `/public/spatial-research/registry`, `/public/spatial-research/handoffs`, `/public/routes/summary`, and `/public/release-gate`. A sample compose + Workspace handoff + package request is included in the deployment verifier.
