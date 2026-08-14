#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts/validate_v43525_release_contract.py")], check=True)
wp = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
index = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
app = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
assert "Version: 4.35.25" in wp and "site-intelligence-v4.35.25" in wp
assert 'data-scsi-release="4.35.25"' in index
assert 'const APP_VERSION="4.35.25"' in app
assert "COUNTRY INTELLIGENCE BRIEF" in index
assert "Operational evidence is separate from structural statistics" in index
assert "OFFICIAL, PUBLISHED & COMPARATIVE INDICATORS" in index
assert "renderCountryEvidenceHierarchy" in app
assert "renderCountryIndicatorCard" in app
assert "4.0 Direction" not in index
for file in (
    "backend/app/country_evidence_presentation_v43525.py",
    "backend/app/release_health_v43525.py",
    "backend/tests/test_country_evidence_presentation_v43525.py",
    "backend/public_app/assets/country-presentation-v43525.css",
    "scripts/validate_v43525_release_contract.py",
    "RELEASE_NOTES_SITE_INTELLIGENCE_V43525.md",
    "SITE_INTELLIGENCE_V43525_COUNTRY_INTELLIGENCE_PRESENTATION_AUDIT.md",
    "SITE_INTELLIGENCE_V43525_INSTALL_AND_TEST.md",
):
    assert (ROOT / file).is_file(), file
print("PASS: v4.35.25 static release validation")
