#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts/validate_v43522_release_contract.py")], check=True)
wp = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
assert "Version: 4.35.23" in wp and "site-intelligence-v4.35.23" in wp
index = (ROOT / "backend/public_app/index.html").read_text()
app = (ROOT / "backend/public_app/assets/app.js").read_text()
assert 'data-scsi-release="4.35.23"' in index
assert 'const APP_VERSION="4.35.23"' in app
assert "Evidence reconciliation & scope integrity" in app
for file in (
    "backend/app/country_evidence_reconciliation_v43522.py",
    "backend/app/release_health_v43522.py",
    "backend/tests/test_country_evidence_reconciliation_v43522.py",
    "backend/tests/test_country_evidence_reconciliation_release_contract_v43522.py",
    "scripts/validate_v43522_release_contract.py",
    "scripts/browser_workspace_e2e_v43522.py",
    "RELEASE_NOTES_SITE_INTELLIGENCE_V43522.md",
    "SITE_INTELLIGENCE_V43522_COUNTRY_EVIDENCE_RECONCILIATION_SCOPE_INTEGRITY_AUDIT.md",
):
    assert (ROOT / file).is_file(), file
print("PASS: v4.35.23 static release validation")
