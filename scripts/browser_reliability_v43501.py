#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
index = (ROOT / "backend/public_app/index.html").read_text()
truth = (ROOT / "backend/public_app/assets/production-truth-v3231.js").read_text()
astro = (ROOT / "backend/public_app/assets/astronomical-observation-v4300.js").read_text()
country = (ROOT / "backend/app/live_country_intelligence.py").read_text()
assert 'data-scsi-release="4.35.1"' in index
assert 'const VERSION="4.35.1"' in truth or "const VERSION='4.35.1'" in truth
assert "configurationRequired" in truth
assert "|unavailable|" not in truth
assert 'exoplanet-habitability-v43500.js?v=4.35.1' in astro
assert '"West Bank and Gaza": "Palestine"' in country
print("PASS: v4.35.1 workspace reliability browser/static asset gate")
