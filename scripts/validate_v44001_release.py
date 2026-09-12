#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "4.40.0.1"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")

version_py = (ROOT / "backend/app/version.py").read_text(encoding="utf-8")
if f'APP_VERSION = "{VERSION}"' not in version_py:
    fail("backend APP_VERSION mismatch")
if 'RELEASE_NAME = "Homepage Live Intelligence Runtime Repair"' not in version_py:
    fail("release name mismatch")

main_py = (ROOT / "backend/app/main.py").read_text(encoding="utf-8")
summary_py = (ROOT / "backend/app/homepage_summary_v4390.py").read_text(encoding="utf-8")
php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text(encoding="utf-8")
css = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text(encoding="utf-8")

required_main = [
    "LIVE_INTELLIGENCE_FEED_REGISTRY",
    "LIVE_INTELLIGENCE_DEFAULT_FEEDS",
    "registered_source_count=len(LIVE_INTELLIGENCE_FEED_REGISTRY)",
    "enabled_source_count=len(LIVE_INTELLIGENCE_DEFAULT_FEEDS)",
]
for marker in required_main:
    if marker not in main_py:
        fail(f"backend runtime count marker missing: {marker}")

for marker in ["registered_source_count", "enabled_source_count", "active Live Intelligence runtime feed registry"]:
    if marker not in summary_py:
        fail(f"homepage summary repair marker missing: {marker}")

for marker in [
    "Version: 4.40.0.1",
    "const VERSION = '4.40.0.1';",
    "site-intelligence-v4.40.0.1",
    "data-status-endpoint",
]:
    if marker not in php:
        fail(f"WordPress identity/runtime marker missing: {marker}")

for marker in [
    "configureTickerTrack",
    "ResizeObserver",
    "--scsi-live-travel",
    "metrics.registered_sources || metrics.live_feeds",
    "liveStatus.available_feeds.length",
    "liveStatus.default_feeds.length",
    "payload.featured_signal_count",
]:
    if marker not in js:
        fail(f"JavaScript repair marker missing: {marker}")

for marker in ['data-scsi-ticker-ready="1"', "translate3d(var(--scsi-live-travel),0,0)"]:
    if marker not in css:
        fail(f"ticker CSS marker missing: {marker}")

# The fixed half-track assumption must be gone from the active ticker keyframe.
keyframe = re.search(r"@keyframes\s+scsi-live-scroll\s*\{([^}]*(?:\}[^}]*)?)\}", css)
if "translateX(-50%)" in css:
    fail("legacy fixed -50% ticker travel remains in CSS")

static_release_files = [
    'analytical_workspace_policy_v3234.json','bootstrap_recovery_policy_v32361.json','briefing_publication_policy_v3290.json',
    'browser_reliability_policy_v3235.json','comparative_model_assurance_policy_v3260.json','connected_platform_policy_v300.json',
    'country_identity_registry_v43523.json','embed_isolation_policy_v32363.json','evidence_synthesis_policy_v2180.json',
    'federation_policy_v2240.json','institutional_review_governance_policy_v3300.json','institutional_workspaces_policy_v2220.json',
    'intelligence_publishing_policy_v2200.json','knowledge_graph_policy_v2190.json','knowledge_graph_relationship_registry_v2190.json',
    'live_intelligence_source_registry_v320.json','map_interaction_policy_v3232.json','model_governance_policy_v2170.json',
    'model_metric_registry_v2170.json','monitoring_early_warning_policy_v3280.json','mutation_observer_recovery_policy_v32362.json',
    'performance_offline_policy_v3236.json','research_evidence_integration_policy_v3270.json','scheduled_monitoring_policy_v2210.json',
    'spatial_evidence_policy_v2150.json','startup_stability_policy_v32364.json','unified_analytical_state_policy_v3250.json',
]
for name in static_release_files:
    p = ROOT / "backend/data" / name
    if not p.is_file():
        fail(f"missing source-reconciled static file: {name}")
    payload = json.loads(p.read_text(encoding="utf-8"))
    if payload.get("version") != VERSION:
        fail(f"{name}: top-level version {payload.get('version')!r} != {VERSION!r}")

print(json.dumps({
    "ok": True,
    "version": VERSION,
    "repair": "homepage-live-intelligence-runtime",
    "static_release_files": len(static_release_files),
    "metric_runtime_binding": True,
    "metric_compatibility_fallback": True,
    "measured_ticker": True,
}, indent=2))
print("PASS: Site Intelligence v4.40.0.1 release contract validated.")
