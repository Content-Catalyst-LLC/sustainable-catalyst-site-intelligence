from pathlib import Path
from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app
from app import offline_mobile_accessibility_performance_v2120 as module

client=TestClient(app)
ROOT=Path(__file__).resolve().parents[2]

def settings(**kwargs):
    base={"offline_experience_enabled":True,"service_worker_enabled":True,"offline_cache_max_entries":120,"offline_cache_ttl_hours":24,"low_bandwidth_default":False}
    base.update(kwargs);return SimpleNamespace(**base)

def test_overview_and_cache_plan_preserve_offline_limits():
    out=module.build_overview(settings());plan=module.build_cache_plan(settings())
    assert out["version"]=="3.16.0" and out["privacy"]["server_profile_storage_added"] is False
    assert plan["enabled"] is True and plan["limits"]["maximum_entries"]==120
    assert plan["strategies"]["writes"]=="network-only"

def test_accessibility_is_target_not_certification_and_performance_is_bounded():
    a=module.build_accessibility(settings());p=module.build_performance(settings())
    assert a["certification"]=="none" and "target" in a["target"].lower()
    assert all(p["budget_checks"].values())

def test_pwa_diagnostics_and_public_routes():
    d=module.build_diagnostics(settings());assert d["ok"] is True
    for path in ["/public/offline-experience","/public/offline-experience/cache-plan","/public/offline-experience/accessibility","/public/offline-experience/performance","/public/offline-experience/diagnostics","/app/manifest.webmanifest","/app/service-worker.js","/app/offline.html"]:
        assert client.get(path).status_code==200
    assert client.get("/app/service-worker.js").headers["cache-control"].startswith("no-cache")

def test_frontend_and_wordpress_contract():
    html=(ROOT/"backend/public_app/index.html").read_text();js=(ROOT/"backend/public_app/assets/experience-v2120.js").read_text();sw=(ROOT/"backend/public_app/service-worker.js").read_text();php=(ROOT/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert 'data-route="experience"' in html and 'id="offlineExperienceStudio"' in html and 'rel="manifest"' in html
    assert "SCExperienceV2120" in js and 'request.method!=="GET"' in sw
    assert "Version: 3.16.0" in php and "sc_offline_mobile_accessibility_performance" in php
