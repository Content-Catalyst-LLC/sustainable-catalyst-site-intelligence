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


version = text("backend/app/version.py")
main = text("backend/app/main.py")
summary = text("backend/app/homepage_summary_v4390.py")
plugin = text("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
javascript = text("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js")
stylesheet = text("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css")
readme = text("README.md")

require('APP_VERSION = "4.39.0"' in version, "backend APP_VERSION is not 4.39.0")
require("Version: 4.39.0" in plugin and "site-intelligence-v4.39.0" in plugin, "WordPress release identity mismatch")
for route in ("/v1/public/site-intelligence/summary", "/public/site-intelligence/summary"):
    require(route in main, f"missing public homepage route {route}")
for token in ("SCHEMA_VERSION", "country_identity_registry_v43523.json", "live_intelligence_source_registry_v320.json", "truth_boundaries", "entry_points"):
    require(token in summary, f"homepage summary contract missing {token}")
require("add_shortcode('sc_site_intelligence_home'" in plugin, "homepage shortcode is not registered")
require("data-scsi-home-summary" in plugin and "v1/public/site-intelligence/summary" in plugin, "homepage shortcode/proxy contract missing")
method = plugin.split("public function site_intelligence_home_shortcode", 1)[1].split("public function", 1)[0]
require("<iframe" not in method, "homepage shortcode must not contain an iframe")
for token in ("setupSiteIntelligenceHomeSummary", "Live summary temporarily unavailable", "no values have been estimated or fabricated"):
    require(token in javascript, f"homepage controller missing {token}")
for token in (".scsi-home-summary__metrics", ".scsi-home-summary__signals", "forced-colors", "prefers-reduced-motion"):
    require(token in stylesheet, f"homepage stylesheet missing {token}")
require("[sc_site_intelligence_home]" in readme and "Homepage Live Intelligence Snapshot" in readme, "README current release documentation missing")
for relative in (
    "backend/tests/test_homepage_summary_v4390.py",
    "RELEASE_NOTES_SITE_INTELLIGENCE_V4390.md",
    "SITE_INTELLIGENCE_V4390_HOME_SHORTCODE_AUDIT.md",
    "SITE_INTELLIGENCE_V4390_INSTALL_AND_TEST.md",
    "SITE_INTELLIGENCE_V4390_TERMINAL_COMMANDS.txt",
):
    require((ROOT / relative).is_file(), f"missing release file {relative}")

if errors:
    for error in errors:
        print("FAIL:", error, file=sys.stderr)
    raise SystemExit(1)
print("PASS: v4.39.0 homepage summary release contract")
