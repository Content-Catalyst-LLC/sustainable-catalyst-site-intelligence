#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT/"scripts/validate_v43519_release_contract.py")], check=True)
wp=(ROOT/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
assert "Version: 4.35.19" in wp and "site-intelligence-v4.35.19" in wp
index=(ROOT/"backend/public_app/index.html").read_text()
app=(ROOT/"backend/public_app/assets/app.js").read_text()
assert 'data-scsi-release="4.35.19"' in index
assert 'const APP_VERSION="4.35.19"' in app
for marker in ("SIMPLY WORKS WORKSPACE AUDIT", "LIVE-OPERATION STRESS LAYER · v4.35.19", "workspace-reliability-v43518.js"):
    assert marker in index, marker
for file in (
    "backend/app/workspace_browser_audit_v43518.py",
    "backend/app/external_resilience_v43517.py",
    "backend/app/production_soak_v43519.py",
    "backend/app/evidence_presentation_v43519.py",
    "backend/app/release_health_v43519.py",
    "backend/tests/test_production_soak_semantic_truth_v43519.py",
    "scripts/validate_v43519_release_contract.py",
):
    assert (ROOT/file).is_file(), file
print("PASS: v4.35.19 static release validation")
