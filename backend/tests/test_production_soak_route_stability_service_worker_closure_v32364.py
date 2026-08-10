from __future__ import annotations
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
ROOT = Path(__file__).resolve().parents[2]
CLIENT = TestClient(app)

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

def test_public_startup_stability_contract():
    payload = CLIENT.get("/public/startup-stability").json()
    assert payload["ok"] is True
    assert payload["version"] == "4.30.0"
    assert payload["startup"]["network_data_blocks_shell"] is False
    assert payload["startup"]["initial_data_strategy"] == "background-all-settled"
    assert payload["service_worker"]["automatic_controllerchange_reload"] is False
    assert payload["wordpress_embed"]["complete_application_loading"] == "eager"

def test_startup_is_not_blocked_by_network_hydration():
    js = read("backend/public_app/assets/app.js")
    assert "launchFinished" in js
    assert 'finishLaunch({message:"Site Intelligence is ready. Public data services are connecting."})' in js
    assert "Promise.allSettled([layerTask,loadEvents(),countryCatalogTask,countryTask,routeTask])" in js
    launch = js.index('finishLaunch({message:"Site Intelligence is ready. Public data services are connecting."})')
    hydrate = js.index("Promise.allSettled([layerTask,loadEvents(),countryCatalogTask,countryTask,routeTask])")
    assert launch < hydrate
    assert "const effectiveAttempts=window.SCSIServiceRecovery?1" in js

def test_route_changes_are_serialized_and_recovery_uses_queue():
    js = read("backend/public_app/assets/app.js")
    for token in ("routeTransitionActive", "pendingRoute", "scsi:route-transition-start", "scsi:route-transition-end", "await navigateToRoute(state.route)"):
        assert token in js

def test_service_worker_has_closed_update_lifecycle():
    worker = read("backend/public_app/service-worker.js")
    bootstrap = read("backend/public_app/assets/bootstrap-v32361.js")
    assert 'event.waitUntil(installCritical())' in worker
    assert 'installCritical().then(()=>self.skipWaiting())' not in worker
    assert 'SC_SI_GET_LIFECYCLE' in worker
    assert 'automaticReloads:0' in bootstrap
    assert 'activateWaitingWorker' in bootstrap
    assert 'location.reload()' not in bootstrap.replace("retry()?.addEventListener('click',()=>location.reload(),{once:true});", "")

def test_wordpress_complete_application_is_eager_and_high_priority():
    php = read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    block = php[php.index("public function standalone_app_shortcode"):php.index("public function geospatial_map_shortcode")]
    assert 'loading="eager"' in block
    assert 'fetchpriority="high"' in block
    assert 'data-scsi-eager-app="1"' in block
    host = read("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js")
    assert "['scsi-height','scsi-bootstrap-ready','scsi-shell-ready']" in host

def test_runtime_health_requires_startup_stability():
    health = CLIENT.get("/public/runtime-health").json()
    assert health["ok"] is True
    assert "/public/startup-stability" in {row["path"] for row in health["endpoint_contracts"]}
    checks = {row["id"]: row for row in health["checks"]}
    assert checks["startup-stability-and-worker-closure"]["status"] == "pass"
