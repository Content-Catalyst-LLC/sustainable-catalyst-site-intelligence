#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.unified_public_intelligence_v4000 import (
    public_unified_platform,
    public_unified_navigation,
    public_unified_contracts,
    public_v4_readiness,
)

platform = public_unified_platform()
nav = public_unified_navigation()
contracts = public_unified_contracts()
ready = public_v4_readiness()
assert platform["version"] == "4.7.0"
assert platform["primary_area_count"] == 6 and platform["route_count"] == 35
assert nav["all_routes_unique"] is True and len(nav["routes"]) == 35
assert contracts["contract_count"] == 6 and contracts["human_review_preserved"] is True
assert ready["ok"] is True and all(ready["checks"].values())
html = (ROOT / "backend/public_app/index.html").read_text()
sw = (ROOT / "backend/public_app/service-worker.js").read_text()
js = (ROOT / "backend/public_app/assets/unified-platform-v4000.js").read_text()
assert 'data-scsi-platform-contract="unified-v4"' in html
assert 'unified-platform-v4000.js?v=4.7.0' in html
assert 'unified-platform-v4000.css?v=4.7.0' in html
assert 'unified-platform-v4000.js' in sw and 'unified-platform-v4000.css' in sw
assert 'SCSIUnifiedPlatformV4000' in js
print(json.dumps({"version":"4.7.0","primary_areas":6,"routes":35,"contracts":6,"readiness":ready["ok"],"platform_sha256":platform["platform_sha256"]},indent=2))
print("PASS: Site Intelligence v4.7.0 Unified Public Intelligence Platform contracts are complete.")
