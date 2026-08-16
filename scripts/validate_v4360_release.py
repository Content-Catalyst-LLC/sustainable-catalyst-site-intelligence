#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts/validate_v4360_release_contract.py")], check=True)
wp = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
index = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
app = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
sw = (ROOT / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
assert "Version: 4.36.0" in wp and "site-intelligence-v4.36.0" in wp
assert 'data-scsi-release="4.36.0"' in index
assert 'const APP_VERSION="4.36.0"' in app
assert 'data-ocean-entry="hub"' in index
assert 'id="oceanObservationStudio"' in index
assert "ocean-observation-v4360.js" in sw and "ocean-observation-v4360.css" in sw
for file in (
    "backend/app/ocean_observation_marine_systems_v4360.py",
    "backend/tests/test_global_ocean_intelligence_ii_v4360.py",
    "backend/public_app/assets/ocean-observation-v4360.css",
    "backend/public_app/assets/ocean-observation-v4360.js",
    "scripts/validate_v4360_release_contract.py",
    "RELEASE_NOTES_SITE_INTELLIGENCE_V4360.md",
    "SITE_INTELLIGENCE_V4360_OCEAN_OBSERVATION_AUDIT.md",
    "SITE_INTELLIGENCE_V4360_INSTALL_AND_TEST.md",
):
    assert (ROOT / file).is_file(), file
print("PASS: v4.36.0 R1 static release validation")
