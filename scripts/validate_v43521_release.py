#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT/"scripts/validate_v43521_release_contract.py")], check=True)
wp=(ROOT/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
assert "Version: 4.35.23" in wp and "site-intelligence-v4.35.23" in wp
index=(ROOT/"backend/public_app/index.html").read_text()
app=(ROOT/"backend/public_app/assets/app.js").read_text()
assert 'data-scsi-release="4.35.23"' in index
assert 'const APP_VERSION="4.35.23"' in app
assert "Country-linked records" in index
for file in (
    "backend/app/authoritative_connectors_v43521.py",
    "backend/app/palestine_data_federation_v43521.py",
    "backend/app/wikimedia_knowledge_context_v43521.py",
    "backend/app/release_health_v43521.py",
    "backend/tests/test_palestine_wikimedia_context_v43521.py",
    "scripts/validate_v43521_release_contract.py",
):
    assert (ROOT/file).is_file(), file
print("PASS: v4.35.23 static release validation")
