#!/usr/bin/env python3
from pathlib import Path
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
manifest_path = ROOT / "MANIFEST.json"
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text())
    assert not any(row["path"].startswith("backend/backend/") for row in manifest.get("files", []))
assert not (ROOT / "backend/backend").exists()

version = (ROOT / "backend/app/version.py").read_text()
assert 'APP_VERSION = "4.35.2"' in version
main = (ROOT / "backend/app/main.py").read_text()
for endpoint in (
    '/public/authoritative-apis',
    '/public/authoritative-apis/catalog',
    '/public/authoritative-apis/workspaces',
    '/public/authoritative-apis/readiness',
    '/public/v4/configuration-readiness',
):
    assert f'@app.get("{endpoint}")' in main

audit = (ROOT / "backend/app/authoritative_api_audit_v4352.py").read_text()
for state in ("LIVE", "DISCOVERY", "REGISTERED", "AUTH_REQUIRED", "BULK", "STALE", "UNAVAILABLE"):
    assert f'"{state}"' in audit
for interface in ("reliefweb-v2", "usgs-water-ogc-v0", "noaa-coastwatch-erddap", "nasa-cmr-search", "nasa-exoplanet-tap", "unhcr-refugee-statistics-v1"):
    assert interface in audit

reliefweb = (ROOT / "backend/app/unified_live_events.py").read_text()
assert '"api_version": "v2"' in reliefweb
assert "https://api.reliefweb.int/v2/reports" in reliefweb
assert "api.reliefweb.int/v1/reports" not in reliefweb
assert "SC_SI_RELIEFWEB_APPNAME" in reliefweb

render = (ROOT / "render.yaml").read_text()
assert "site-intelligence-v4.35.2" in render
assert "SC_SI_RELIEFWEB_APPNAME" in render
for key in ("SC_SI_PLATFORM_CORE_ENABLED", "SC_SI_PLATFORM_CORE_URL", "SC_SI_PLATFORM_CORE_PUBLIC_API_KEY"):
    assert key in render

index = (ROOT / "backend/public_app/index.html").read_text()
app_js = (ROOT / "backend/public_app/assets/app.js").read_text()
assert "AUTHORITATIVE API COVERAGE" in index
for token in ("authoritativeRegistrationMetric", "authoritativeLiveMetric", "authoritativeGapMetric", "authoritativeAuthMetric", "authoritativePriorityTargets"):
    assert token in index
assert "/public/authoritative-apis" in app_js
assert "renderAuthoritativeApiAudit" in app_js

plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
assert "Version: 4.35.2" in plugin
assert "site-intelligence-v4.35.2" in plugin

subprocess.run(
    [sys.executable, str(ROOT / "scripts/validate_v43502_release_contract.py")],
    check=True,
    cwd=ROOT,
    env={**os.environ, "PYTHONPATH": str(ROOT / "backend")},
)
print("PASS: v4.35.2 static release validation")
