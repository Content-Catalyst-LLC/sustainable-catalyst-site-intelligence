#!/usr/bin/env python3
from pathlib import Path
import json
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.main import app

required = {
    "backend/app/version.py": ['APP_VERSION = "4.16.0"'],
    "backend/app/embed_isolation_v32363.py": ["public_embed_isolation_contract"],
    "backend/data/embed_isolation_policy_v32363.json": ["fixed-application-viewport-and-wordpress-embed-isolation", "document_auto_resize"],
    "backend/public_app/assets/embed-isolation-v32363.js": ["SCSI_FIXED_WORDPRESS_EMBED", "wordpress-fixed", "heightMessagesEnabled"],
    "backend/public_app/assets/embed-isolation-v32363.css": ["scsi-wordpress-fixed-embed", "overflow:hidden", "overflow-y:auto"],
    "backend/public_app/assets/app.js": ["FIXED_WORDPRESS_EMBED", "if(FIXED_WORDPRESS_EMBED)return"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 4.16.0", "data-scsi-fixed-app", 'data-scsi-release="%5$s"'],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": ["enforceFixedViewport", "if (!record.fixed) applyHeight", "syncSiteIntelligencePublicRelease"],
    "scripts/browser_wordpress_embed_gate_v32363.py": ["ERROR: Chromium or Chrome is required", "scrollHeight", "frameHeight"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V32363.md": ["Fixed Application Viewport and WordPress Embed Isolation"],
}
for relative, tokens in required.items():
    path = ROOT / relative
    if not path.is_file():
        raise SystemExit(f"Missing {relative}")
    text = path.read_text(encoding="utf-8")
    for token in tokens:
        if token not in text:
            raise SystemExit(f"Missing {token!r} in {relative}")

client = TestClient(app)
contract = client.get("/public/embed-isolation").json()
if not contract.get("ok") or contract.get("version") != "4.16.0" or contract.get("application_embed", {}).get("document_auto_resize") is not False:
    raise SystemExit("Embed isolation endpoint failed.")
health = client.get("/public/runtime-health").json()
checks = {row["id"]: row for row in health.get("checks", [])}
if not health.get("ok") or checks.get("fixed-wordpress-embed-isolation", {}).get("status") != "pass":
    raise SystemExit("Runtime embed isolation check failed.")
manifest_path = ROOT / "MANIFEST.json"
if manifest_path.is_file():
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("release") != "4.16.0":
        raise SystemExit("Manifest release mismatch.")
print("Site Intelligence v4.16.0 fixed application viewport and WordPress embed isolation contract passed.")
