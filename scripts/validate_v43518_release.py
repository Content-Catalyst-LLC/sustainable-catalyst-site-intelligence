#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT/"scripts/validate_v43518_release_contract.py")], check=True)
wp=(ROOT/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
assert "Version: 4.35.20" in wp and "site-intelligence-v4.35.20" in wp
index=(ROOT/"backend/public_app/index.html").read_text()
app=(ROOT/"backend/public_app/assets/app.js").read_text()
assert 'data-scsi-release="4.35.20"' in index
assert 'const APP_VERSION="4.35.20"' in app
for marker in ("SIMPLY WORKS WORKSPACE AUDIT", "workspace-reliability-v43518.js"):
    assert marker in index, marker
for file in (
    "backend/app/workspace_browser_audit_v43518.py",
    "backend/app/release_health_v43518.py",
    "backend/public_app/assets/workspace-reliability-v43518.js",
    "backend/tests/test_workspace_browser_audit_v43518.py",
    "scripts/browser_workspace_e2e_v43518.py",
):
    assert (ROOT/file).is_file(), file
print("PASS: v4.35.20 static release validation")
