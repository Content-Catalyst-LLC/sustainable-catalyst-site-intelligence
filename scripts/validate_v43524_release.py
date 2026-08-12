#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts/validate_v43524_release_contract.py")], check=True)
wp = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
assert "Version: 4.35.24" in wp and "site-intelligence-v4.35.24" in wp
index = (ROOT / "backend/public_app/index.html").read_text()
app = (ROOT / "backend/public_app/assets/app.js").read_text()
cartography = (ROOT / "backend/public_app/assets/cartographic-workspace-v3230.js").read_text()
registry = json.loads((ROOT / "backend/data/country_identity_registry_v43523.json").read_text())
rows = {row["code"]: row for row in registry["countries"]}
assert 'data-scsi-release="4.35.24"' in index
assert 'const APP_VERSION="4.35.24"' in app
assert "Country identity mismatch blocked" in app
assert "history.replaceState" in app
assert "canonical coordinates" in app.lower() or "first-party canonical" in app.lower()
assert "...item,...canonical" in cartography.replace(" ", "") or "...item, ...canonical" in cartography
assert rows["ISR"]["name"] == "Israel" and rows["ISR"]["iso2"] == "IL"
assert rows["PSE"]["name"] == "Palestine" and rows["PSE"]["iso2"] == "PS"
for file in (
    "backend/app/country_navigation_integrity_v43524.py",
    "backend/app/release_health_v43524.py",
    "backend/tests/test_country_navigation_integrity_v43524.py",
    "scripts/validate_v43524_release_contract.py",
    "scripts/browser_palestine_navigation_integrity_v43524.py",
    "scripts/browser_workspace_e2e_v43524.py",
    "RELEASE_NOTES_SITE_INTELLIGENCE_V43524.md",
    "SITE_INTELLIGENCE_V43524_COUNTRY_NAVIGATION_INTEGRITY_AUDIT.md",
    "SITE_INTELLIGENCE_V43524_INSTALL_AND_TEST.md",
):
    assert (ROOT / file).is_file(), file
print("PASS: v4.35.24 static release validation")
