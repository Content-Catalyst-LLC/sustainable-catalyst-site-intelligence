#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

def require(condition, message):
    if not condition:
        errors.append(message)

def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")

version = text("backend/app/version.py")
main = text("backend/app/main.py")
summary = text("backend/app/homepage_summary_v4391.py")
plugin = text("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
js = text("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js")
css = text("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css")
readme = text("README.md")

require('APP_VERSION = "4.39.1"' in version, "backend APP_VERSION is not 4.39.1")
require("Version: 4.39.1" in plugin and "const VERSION = '4.39.1';" in plugin and "site-intelligence-v4.39.1" in plugin, "WordPress release identity mismatch")
require("from .homepage_summary_v4391 import build_homepage_summary" in main, "main.py does not use v4.39.1 homepage summary")
for route in ("/v1/public/site-intelligence/summary", "/public/site-intelligence/summary"):
    require(route in main, f"missing public homepage route {route}")
for token in ("enabled_connectors", "public_workspaces", "live_feeds", "PUBLIC_WORKSPACE_COUNT = 35", "truth_boundaries"):
    require(token in summary, f"homepage summary contract missing {token}")
method = plugin.split("public function site_intelligence_home_shortcode", 1)[1].split("public function", 1)[0]
require("data-home-metric-slot" in method, "homepage shortcode does not use schema-tolerant metric slots")
require("registered_sources" not in method and "enabled_sources" not in method and "current_signals" not in method, "homepage shortcode still hardcodes v4.39.1 metric IDs")
for token in ("safeItemHtml", "renderMinimalFallback", "feed_render_failure", "scsi:live-intelligence-render-error", "Site Intelligence Live Intelligence fetch failed."):
    require(token in js, f"ticker rendering recovery missing {token}")
require(".trimEnd()" not in js, "ticker still depends on String.trimEnd")
require("CSS.escape(String(metric.id" not in js and "metricCards" in js, "homepage metric renderer remains coupled to metric IDs/CSS.escape")
for token in (".scsi-live-intelligence", ".scsi-home-summary__metrics", "prefers-reduced-motion"):
    require(token in css, f"homepage/ticker stylesheet missing {token}")
require("v4.39.1 — Homepage Live Intelligence Asset Integrity & Rendering Recovery" in readme, "README current release documentation missing")
backend_assets = ROOT / "backend/public_app/assets"
wordpress_assets = ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets"
common_asset_names = sorted({path.name for path in backend_assets.iterdir() if path.is_file()} & {path.name for path in wordpress_assets.iterdir() if path.is_file()})
for asset_name in common_asset_names:
    require((backend_assets / asset_name).read_bytes() == (wordpress_assets / asset_name).read_bytes(), f"backend/WordPress browser asset mirror mismatch: {asset_name}")
asset_manifest = ROOT / "WORDPRESS_ASSET_MANIFEST_V4391.json"
require(asset_manifest.is_file(), "WORDPRESS_ASSET_MANIFEST_V4391.json missing")
if asset_manifest.is_file():
    manifest = json.loads(asset_manifest.read_text(encoding="utf-8"))
    for relative, expected in manifest.get("assets", {}).items():
        path = ROOT / relative
        require(path.is_file(), f"asset manifest path missing: {relative}")
        if path.is_file():
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            require(actual == expected, f"asset checksum mismatch: {relative}")
for relative in (
    "backend/tests/test_homepage_summary_v4391.py",
    "backend/tests/test_homepage_live_intelligence_asset_recovery_v4391.py",
    "RELEASE_NOTES_SITE_INTELLIGENCE_V4391.md",
    "SITE_INTELLIGENCE_V4391_ASSET_INTEGRITY_AUDIT.md",
    "SITE_INTELLIGENCE_V4391_INSTALL_AND_TEST.md",
    "SITE_INTELLIGENCE_V4391_TERMINAL_COMMANDS.txt",
):
    require((ROOT / relative).is_file(), f"missing release file {relative}")
if errors:
    for error in errors:
        print("FAIL:", error, file=sys.stderr)
    raise SystemExit(1)
print("PASS: v4.39.1 homepage ticker asset-integrity and rendering-recovery contract")
