#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "4.40.0.3"


def fail(msg):
    raise SystemExit(f"FAIL: {msg}")


def text(path):
    return (ROOT / path).read_text(encoding="utf-8")

version_py = text("backend/app/version.py")
if f'APP_VERSION = "{VERSION}"' not in version_py:
    fail("backend APP_VERSION mismatch")
if 'RELEASE_NAME = "Live Intelligence Ticker Pace & Readability Repair"' not in version_py:
    fail("release name mismatch")

summary_py = text("backend/app/homepage_summary_v4390.py")
for marker in [
    "enabled_connectors",
    "public_workspaces",
    "live_feeds",
    "featured_signal_count",
    "connector_operations_registry_v2130.json",
    "unified_public_intelligence_policy_v4000.json",
]:
    if marker not in summary_py:
        fail(f"summary marker missing: {marker}")
for forbidden in ["registered_sources", "enabled_sources", "current_signals"]:
    if f'"id": "{forbidden}"' in summary_py:
        fail(f"superseded metric still active: {forbidden}")

php = text("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
js = text("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js")
css = text("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css")
for marker in [
    "Version: 4.40.0.3",
    "const VERSION = '4.40.0.3';",
    "site-intelligence-v4.40.0.3",
    "data-home-live-ticker",
    "['enabled_connectors', 'enabled connectors']",
    "['public_workspaces', 'public workspaces']",
    "['live_feeds', 'live ticker feeds']",
]:
    if marker not in php:
        fail(f"WordPress marker missing: {marker}")

for marker in [
    "renderMetric('enabled_connectors', metrics.enabled_connectors)",
    "renderMetric('public_workspaces', metrics.public_workspaces)",
    "renderMetric('live_feeds', metrics.live_feeds)",
    "const calculateTickerPace = function (travel)",
    "const targetPixelsPerSecond = mobileQuery.matches ? 23 : 28;",
    "const minimumDurationSeconds = mobileQuery.matches ? 90 : 75;",
    "const maximumDurationSeconds = mobileQuery.matches ? 260 : 220;",
    "const measuredDurationSeconds = travel / targetPixelsPerSecond;",
    "track.style.setProperty('--scsi-live-duration', durationValue)",
    "track.style.setProperty('--scsi-live-mobile-duration', durationValue)",
    "root.dataset.scsiTickerPixelsPerSecond",
    "root.dataset.scsiTickerDurationSeconds",
    "root.dataset.scsiTickerTravelPixels",
    "configureTickerTrack",
    "setupLiveIntelligence();",
]:
    if marker not in js:
        fail(f"JavaScript marker missing: {marker}")

for forbidden in ["liveStatus.available_feeds.length", "liveStatus.default_feeds.length"]:
    if forbidden in js:
        fail(f"wrong metric fallback remains: {forbidden}")

for marker in [
    "scsi-home-summary__live-ticker",
    'data-scsi-ticker-ready="1"',
    "translate3d(var(--scsi-live-travel),0,0)",
    "--scsi-live-duration:96s;",
    "--scsi-live-mobile-duration:118s;",
]:
    if marker not in css:
        fail(f"ticker CSS marker missing: {marker}")
for forbidden in ["--scsi-live-duration:42s;", "--scsi-live-mobile-duration:36s;", "translateX(-50%)"]:
    if forbidden in css:
        fail(f"legacy ticker pacing/travel remains: {forbidden}")

data = ROOT / "backend/data"
connectors = json.loads((data / "connector_operations_registry_v2130.json").read_text(encoding="utf-8"))["connectors"]
policy = json.loads((data / "unified_public_intelligence_policy_v4000.json").read_text(encoding="utf-8"))
sources = json.loads((data / "live_intelligence_source_registry_v320.json").read_text(encoding="utf-8"))["sources"]
countries = json.loads((data / "country_identity_registry_v43523.json").read_text(encoding="utf-8"))["countries"]
routes = {route for area in policy["primary_areas"] for route in area.get("routes", [])}
counts = {
    "country_profiles": len(countries),
    "enabled_connectors": sum(1 for x in connectors if x.get("enabled") is True),
    "public_workspaces": len(routes),
    "live_feeds": len(sources),
}
expected = {"country_profiles": 172, "enabled_connectors": 14, "public_workspaces": 35, "live_feeds": 8}
if counts != expected:
    fail(f"homepage capability contract changed unexpectedly: {counts}")

static_files = [
    'analytical_workspace_policy_v3234.json','bootstrap_recovery_policy_v32361.json','briefing_publication_policy_v3290.json','browser_reliability_policy_v3235.json','comparative_model_assurance_policy_v3260.json','connected_platform_policy_v300.json','country_identity_registry_v43523.json','embed_isolation_policy_v32363.json','evidence_synthesis_policy_v2180.json','federation_policy_v2240.json','institutional_review_governance_policy_v3300.json','institutional_workspaces_policy_v2220.json','intelligence_publishing_policy_v2200.json','knowledge_graph_policy_v2190.json','knowledge_graph_relationship_registry_v2190.json','live_intelligence_source_registry_v320.json','map_interaction_policy_v3232.json','model_governance_policy_v2170.json','model_metric_registry_v2170.json','monitoring_early_warning_policy_v3280.json','mutation_observer_recovery_policy_v32362.json','performance_offline_policy_v3236.json','research_evidence_integration_policy_v3270.json','scheduled_monitoring_policy_v2210.json','spatial_evidence_policy_v2150.json','startup_stability_policy_v32364.json','unified_analytical_state_policy_v3250.json'
]
for name in static_files:
    payload = json.loads((data / name).read_text(encoding="utf-8"))
    if payload.get("version") != VERSION:
        fail(f"{name}: release version mismatch")

print(json.dumps({
    "ok": True,
    "version": VERSION,
    "repair": "live-intelligence-ticker-pace-and-readability",
    "capability_metrics": counts,
    "desktop_target_pixels_per_second": 28,
    "mobile_target_pixels_per_second": 23,
    "desktop_duration_bounds_seconds": [75, 220],
    "mobile_duration_bounds_seconds": [90, 260],
    "css_fallback_duration_seconds": {"desktop": 96, "mobile": 118},
    "measured_ticker": True,
    "static_release_files": len(static_files),
}, indent=2))
print("PASS: Site Intelligence v4.40.0.3 release contract validated.")
