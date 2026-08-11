#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT/"scripts/validate_v4354_release_contract.py")], check=True)
wp=(ROOT/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
assert "Version: 4.35.4" in wp
assert "SC_SITE_INTELLIGENCE_VERSION', '4.35.4'" in wp or 'SC_SITE_INTELLIGENCE_VERSION", "4.35.4"' in wp or "4.35.4" in wp
index=(ROOT/"backend/public_app/index.html").read_text()
app=(ROOT/"backend/public_app/assets/app.js").read_text()
assert 'data-scsi-release="4.35.4"' in index
assert 'const APP_VERSION="4.35.4"' in app
assert (ROOT/"backend/app/release_health_v43531.py").is_file()
assert (ROOT/"backend/tests/test_release_gate_source_health_v43531.py").is_file()
assert (ROOT/"backend/app/authoritative_connectors_v4354.py").is_file()
assert (ROOT/"backend/app/authoritative_api_audit_v4354.py").is_file()
assert (ROOT/"backend/tests/test_authoritative_connector_expansion_v4354.py").is_file()
print("PASS: v4.35.4 static release validation")
