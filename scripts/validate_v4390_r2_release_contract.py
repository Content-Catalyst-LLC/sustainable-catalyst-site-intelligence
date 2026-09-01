#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
errors = []


def require(condition, message):
    if not condition:
        errors.append(message)


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


summary = text("backend/app/homepage_summary_v4390.py")
tests = text("backend/tests/test_homepage_summary_v4390.py")
plugin = text("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
javascript = text("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js")
stylesheet = text("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css")
readme = text("README.md")

require('APP_VERSION = "4.39.0"' in text("backend/app/version.py"), "R2 backend identity must remain 4.39.0")
require("Version: 4.39.0" in plugin, "R2 WordPress identity must remain 4.39.0")
for token in (
    "connector_operations_registry_v2130.json",
    "unified_public_intelligence_policy_v4000.json",
    "enabled_connectors",
    "public_workspaces",
    "live_feeds",
    "featured_signal_count",
):
    require(token in summary, f"R2 summary contract missing {token}")
for token in ("enabled_connectors", "public_workspaces", "live_feeds", "featured_signal_count"):
    require(token in tests, f"R2 summary tests missing {token}")
for token in ("enabled_connectors", "public_workspaces", "live_feeds", "limit' => '16'", "data-home-signal-count"):
    require(token in plugin, f"R2 homepage shortcode missing {token}")
require("data-home-signal-count" in javascript and "featured_signal_count" in javascript, "R2 signal count controller missing")
for token in (".scsi-home-summary__signals-head", "min-height:210px", "min-height:128px", "min-height:78px"):
    require(token in stylesheet, f"R2 compact stylesheet missing {token}")
require("v4.39.0 R2" in readme and "Compact Capability Console" in readme, "README R2 release documentation missing")
for relative in (
    "RELEASE_NOTES_SITE_INTELLIGENCE_V4390_R2.md",
    "SITE_INTELLIGENCE_V4390_R2_INSTALL_AND_TEST.md",
    "SITE_INTELLIGENCE_V4390_R2_BUILD_VALIDATION.txt",
    "SITE_INTELLIGENCE_V4390_R2_TERMINAL_COMMANDS.txt",
):
    require((ROOT / relative).is_file(), f"missing R2 release file {relative}")

if errors:
    for error in errors:
        print("FAIL:", error, file=sys.stderr)
    raise SystemExit(1)
print("PASS: v4.39.0 R2 compact layout, capability metrics, ticker breadth, and release-gate contract")
