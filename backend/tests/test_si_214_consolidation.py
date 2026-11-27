"""SI-2.1.4 regression boundaries; fixtures are synthetic, never live source claims."""
import pytest
from fastapi.routing import APIRoute
from app.main import app
from app.route_registry_v4430 import route_inventory
from app.api_reliability_v455311 import normalize_reliable_payload, _public_source_attribution

ENERGY = {("GET", "/v1/energy-spatial/framework"), ("GET", "/v1/energy-spatial/source-registry"),
          ("POST", "/v1/energy-spatial/profile"), ("POST", "/v1/energy-spatial/compare"),
          ("POST", "/v1/energy-spatial/validate-result")}

def test_five_tracked_energy_routes_explain_stale_inventory():
    routes = route_inventory(app.routes)
    energy = [r for r in routes if r["source_module"] == "app.energy_spatial_global_v4410"]
    assert {(m,r["path"]) for r in energy for m in r["methods"]} == ENERGY
    assert all(r["capability_id"] == "infrastructure-energy" for r in energy)
    assert len(routes) == 1530 and len(routes) - len(energy) == 1525
    registrations = [(m,r["path"]) for r in routes for m in r["methods"]]
    assert len(registrations) == len(set(registrations))
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path.startswith("/v1/energy-spatial/"):
            # Existing public request-local analysis; no credential-bearing API exposure added.
            assert not route.dependant.dependencies

@pytest.mark.parametrize("extra", [
    {"records": []}, {"records": [None]}, {"records": [{}]}, {"ok": False},
    {"failure": {"type": "synthetic"}},
    {"integration": {"state": "source-fallback", "configured": False}},
])
def test_invalid_fallback_is_not_promoted(extra):
    payload = {"ok": True, "integration": {"state": "source-fallback", "configured": True},
               "records": [{"id": "synthetic"}]}
    payload.update(extra)
    result, status = normalize_reliable_payload(payload, capability="economics")
    assert status == 503 and result["ok"] is False

def test_attribution_does_not_expose_provider_messages():
    result = _public_source_attribution({"source_states": {
        "world-bank": {"state": "live", "record_count": 2, "message": "private-marker"},
        "invalid://source": "live"}})
    assert result == [{"source":"world-bank", "state":"live", "record_count":2}]
