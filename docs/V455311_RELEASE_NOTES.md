# Site Intelligence v4.55.3.1.1 — Release Notes

Corrective reliability release. No new provider or domain capability is introduced.

The release removes disagreement between `/public/capability-health?probe=true` and the canonical reliable domain routes by routing both through the same probe implementation. Expected upstream/runtime failures are normalized to structured JSON. Science country context no longer passes an unsupported `geography_code` argument. Country aliases are resolved through the canonical first-party country registry. `/ready` now reports both Platform Core reachability and domain operability.
