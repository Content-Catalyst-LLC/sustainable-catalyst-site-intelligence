#!/usr/bin/env python3
from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.main import app  # noqa: E402

c = TestClient(app)
overview = c.get("/public/ocean-observation").json()
catalog = c.get("/public/ocean-observation/catalog").json()
ready = c.get("/public/ocean-observation/readiness").json()
manifest = c.get("/public/ocean-observation/manifest").json()
nav = c.get("/public/v4/navigation").json()
assert overview["ok"] and overview["version"] == "4.39.0" and overview["system_count"] == 11
assert overview["route"] == "earth" and overview["public_route_count_delta"] == 0
assert catalog["system_count"] == 11 and catalog["source_registration_count"] >= 40 and catalog["unique_source_count"] >= 30
assert ready["ok"] and ready["network_calls_performed"] is False and ready["inherited_route_count"] == 35
assert len(ready["systems"]) == 11 and all(row["ok"] for row in ready["systems"].values())
assert manifest["review"]["ocean_navigation_is_first_class"] is True
assert manifest["review"]["new_public_route_created"] is False
assert nav["route_count"] == 35 and nav["primary_area_count"] == 6
index = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
assert 'data-ocean-entry="hub" data-nav-group="analysis" data-nav-after-route="earth" data-nav-featured="true" data-route-alias="earth"' in index and "Open Ocean Intelligence" in index
assert 'data-space-entry="hub" data-nav-group="places-systems" data-nav-after-route="science" data-nav-featured="true" data-route-alias="science"' in index
assert "Explore Ocean" in index and "Explore Space" in index and "Open Space Intelligence" in index
assert 'ocean-observation-v4360.js?v=4.39.0' in index and 'ocean-observation-v4360.css?v=4.39.0' in index
unified = (ROOT / "backend/public_app/assets/unified-platform-v4000.js").read_text(encoding="utf-8")
assert '.nav-item[data-nav-group]:not([data-route])' in unified
assert 'item.dataset.navAfterRoute===route' in unified
assert 'featuredWrap.className="v4000-nav-featured"' in unified
cartographic = (ROOT / "backend/public_app/assets/cartographic-workspace-v3230.js").read_text(encoding="utf-8")
assert ".nav-item.active[data-route-alias]" in cartographic
ocean_js = (ROOT / "backend/public_app/assets/ocean-observation-v4360.js").read_text(encoding="utf-8")
assert 'await Promise.resolve(window.SCSIRouterV3228?.navigate?.("earth"))' in ocean_js
assert 'panel.dataset.oceanWorkspaceOwner="earth:ocean"' in ocean_js
shell_gate = (ROOT / "scripts/browser_complete_shell_gate_v32362.py").read_text(encoding="utf-8")
assert "'/public/ocean-observation/catalog'" in shell_gate and "'/public/ocean-observation/readiness'" in shell_gate
assert (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/unified-platform-v4000.js").read_bytes() == (ROOT / "backend/public_app/assets/unified-platform-v4000.js").read_bytes()
assert (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/unified-platform-v4000.css").read_bytes() == (ROOT / "backend/public_app/assets/unified-platform-v4000.css").read_bytes()
science=(ROOT / "backend/public_app/assets/science-v240.js").read_text(encoding="utf-8")
assert 'panel?.dataset.oceanHydrationState==="ready"' in science
assert 'cards===11' in science
assert 'scsi:ocean-observation-ready' in ocean_js
assert 'dataset.oceanHydrationState="ready"' in ocean_js
app_js=(ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
assert 'async function openFeaturedScienceDomain(domain="space")' in app_js
assert 'openFeaturedScienceDomain("space")' in app_js
science=(ROOT / "backend/public_app/assets/science-v240.js").read_text(encoding="utf-8")
assert 'function openDomain(domain)' in science
assert 'setDomainNav(domain)' in science
production=(ROOT / "backend/public_app/assets/production-truth-v3231.js").read_text(encoding="utf-8")
assert "route==='earth'&&oceanModeActive()" in production
assert "cards!==11" in production
print("PASS: v4.39.0 R4 Science/Ocean controller, route ownership and Ocean/Space prominence release contract")
