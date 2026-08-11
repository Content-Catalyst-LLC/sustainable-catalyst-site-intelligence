#!/usr/bin/env python3
from pathlib import Path
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
manifest_path = ROOT / "MANIFEST.json"
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text())
    assert not any(row["path"].startswith("backend/backend/") for row in manifest.get("files", []))
assert not (ROOT / "backend/backend").exists()

country = (ROOT / "backend/app/live_country_intelligence.py").read_text()
assert '"West Bank and Gaza": "Palestine"' in country
assert '"PSE": ["Palestine", "State of Palestine", "Palestinian Territories", "Palestinian Territory", "West Bank and Gaza"]' in country
assert '"PSE": {"name": "West Bank and Gaza", "iso2": "PS"' in country
assert "def matches(item: dict[str, Any]) -> bool:" in country

unified = (ROOT / "backend/app/unified_public_intelligence_v4000.py").read_text()
assert 'CORE_REQUIRED_ROUTES = ("economics", "law", "science", "resources")' in unified
assert "public_v4_configuration_readiness" in unified
main = (ROOT / "backend/app/main.py").read_text()
assert '@app.get("/public/v4/configuration-readiness")' in main

render = (ROOT / "render.yaml").read_text()
for key in ("SC_SI_PLATFORM_CORE_ENABLED", "SC_SI_PLATFORM_CORE_URL", "SC_SI_PLATFORM_CORE_PUBLIC_API_KEY"):
    assert key in render

truth = (ROOT / "backend/public_app/assets/production-truth-v3231.js").read_text()
assert "configurationRequired" in truth
assert "|unavailable|" not in truth

plugin_truth = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/production-truth-v3231.js").read_text()
assert "configurationRequired" in plugin_truth
assert "|unavailable|" not in plugin_truth

for asset in (
    "exoplanet-habitability-v43500.js",
    "exoplanet-habitability-v43500.css",
    "astronomical-observation-v4300.js",
    "astronomical-observation-v4300.css",
):
    assert (ROOT / "backend/public_app/assets" / asset).read_text() == (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets" / asset).read_text(), asset

subprocess.run(
    [sys.executable, str(ROOT / "scripts/validate_v43501_release_contract.py")],
    check=True,
    cwd=ROOT,
    env={**os.environ, "PYTHONPATH": str(ROOT / "backend")},
)
print("PASS: v4.35.1 static release validation")
