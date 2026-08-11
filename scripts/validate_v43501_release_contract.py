#!/usr/bin/env python3
from pathlib import Path
from types import SimpleNamespace
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import live_country_intelligence as countries
from app import unified_public_intelligence_v4000 as unified
from app.main import app
from app.version import APP_VERSION

assert APP_VERSION == "4.35.1"

pse = countries._normalized_static_catalog()["PSE"]
assert pse["name"] == "Palestine"
assert pse["iso2"] == "PS"
assert {"State of Palestine", "Palestinian Territories", "Palestinian Territory", "West Bank and Gaza"} <= set(pse["alternate_names"])

original_catalog = countries.country_catalog
try:
    countries.country_catalog = lambda *args, **kwargs: {"countries": [{"code": "PSE", **pse}]}
    for alias in ("PSE", "PS", "Palestine", "State of Palestine", "Palestinian Territories", "Palestinian Territory", "West Bank and Gaza"):
        code, metadata = countries._country(alias)
        assert code == "PSE"
        assert metadata["name"] == "Palestine"
finally:
    countries.country_catalog = original_catalog

values = {
    "platform_core_enabled": False,
    "platform_core_url": "",
    "platform_core_public_api_key": "",
    "platform_core_write_api_key": "",
}
for attribute in unified.WORKSPACE_FLAG_MAP.values():
    values[attribute] = True
unconfigured = SimpleNamespace(**values)
r = unified.public_v4_readiness(unconfigured)
assert r["ok"] is True
assert r["runtime_ready"] is False
assert r["runtime_configuration"]["core_required_routes_unavailable"] == ["economics", "law", "science", "resources"]

values["platform_core_enabled"] = True
values["platform_core_url"] = "https://core.example.test"
configured = SimpleNamespace(**values)
cr = unified.public_v4_configuration_readiness(configured)
assert cr["runtime_ready"] is True
assert cr["core_required_routes_unavailable"] == []
assert cr["platform_core"]["public_read_configured"] is True

client = TestClient(app)
api = client.get("/public/v4/configuration-readiness")
assert api.status_code == 200
body = api.json()
assert body.get("ok") is True and body.get("version") == "4.35.1"
assert body.get("contract") == "site-intelligence-runtime-configuration"
assert "platform_core" in body and "required_environment" in body
assert "write_api_key" not in body.get("platform_core", {})
assert "public_api_key" not in body.get("platform_core", {})

exo = client.get("/public/exoplanet-habitability").json()
assert exo.get("ok") and exo.get("version") == "4.35.1"
assert exo.get("contract") == "exoplanets-habitability-atmospheric-biosignature-intelligence"
print("PASS: v4.35.1 country-resolution and workspace-configuration release contract")
