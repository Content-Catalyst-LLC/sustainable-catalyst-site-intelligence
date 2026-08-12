#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts/validate_v43523_release_contract.py")], check=True)
wp = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
assert "Version: 4.35.23" in wp and "site-intelligence-v4.35.23" in wp
index = (ROOT / "backend/public_app/index.html").read_text()
app = (ROOT / "backend/public_app/assets/app.js").read_text()
cartography = (ROOT / "backend/public_app/assets/cartographic-workspace-v3230.js").read_text()
registry = json.loads((ROOT / "backend/data/country_identity_registry_v43523.json").read_text())
rows = {row["code"]: row for row in registry["countries"]}
assert 'data-scsi-release="4.35.23"' in index
assert 'const APP_VERSION="4.35.23"' in app
assert "Country identity mismatch blocked" in app
assert "history.replaceState" in app
assert "/public/data-truth/countries" in cartography and "/public/countries" in cartography
assert rows["ISR"]["name"] == "Israel" and rows["ISR"]["iso2"] == "IL"
assert rows["PSE"]["name"] == "Palestine" and rows["PSE"]["iso2"] == "PS"
for file in (
    "backend/app/country_identity_v43523.py",
    "backend/app/release_health_v43523.py",
    "backend/data/country_identity_registry_v43523.json",
    "backend/tests/test_country_identity_selector_routing_v43523.py",
    "backend/tests/test_country_identity_release_contract_v43523.py",
    "scripts/validate_v43523_release_contract.py",
    "scripts/browser_country_identity_routing_v43523.py",
    "scripts/browser_workspace_e2e_v43523.py",
    "RELEASE_NOTES_SITE_INTELLIGENCE_V43523.md",
    "SITE_INTELLIGENCE_V43523_COUNTRY_IDENTITY_SELECTOR_ROUTING_AUDIT.md",
):
    assert (ROOT / file).is_file(), file
print("PASS: v4.35.23 static release validation")
