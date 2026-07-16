from pathlib import Path
from types import SimpleNamespace
from fastapi.testclient import TestClient
from app import trade_energy_resource_security_observatory as module
from app.main import app
client=TestClient(app)
def settings(**overrides):
    values={"platform_core_enabled":True,"platform_core_url":"https://core.example.test","platform_core_public_api_key":"test-public-key","trade_energy_resource_security_enabled":True,"trade_energy_resource_security_timeout_seconds":9,"trade_energy_resource_security_cache_ttl_seconds":120};values.update(overrides);return SimpleNamespace(**values)
def fake_core(config,path,query=None,**kwargs):
    return {"data":[
      {"id":"trade-1","source_id":"un-comtrade","record_type":"trade_statistic","indicator_code":"IMPORTS","indicator_name":"Merchandise imports","geography_code":"KEN","counterpart_code":"CHN","period":"2025","value_number":100,"unit":"USD million","frequency":"annual","source_url":"https://example.test/trade?api_key=hidden"},
      {"id":"energy-1","source_id":"eia","record_type":"energy_statistic","indicator_code":"ELEC_GEN","indicator_name":"Renewable electricity generation","geography_code":"KEN","period":"2025","value_number":50,"unit":"GWh","frequency":"monthly","source_url":"https://example.test/energy?token=hidden"},
      {"id":"water-1","source_id":"faostat","record_type":"official_statistic","indicator_code":"WATER_STRESS","indicator_name":"Water stress","geography_code":"KEN","period":"2024","value_number":22,"unit":"percent","notes":"AQUASTAT water resource indicator"}
    ],"meta":{"pagination":{"total":3}}}
def test_sanitizes_and_classifies(monkeypatch):
    monkeypatch.setattr(module,"_core_json",fake_core);payload=module.build_records(settings(),limit=20)
    assert {r["family"] for r in payload["records"]}>={"trade","energy","water"}
    assert "api_key" not in str(payload) and "token" not in str(payload) and "test-public-key" not in str(payload)
def test_dependency_view_preserves_counterpart_without_score(monkeypatch):
    monkeypatch.setattr(module,"_core_json",fake_core);payload=module.build_dependencies(settings(),geography_code="KEN")
    assert payload["exposures"][0]["counterpart_code"]=="CHN"
    assert payload["methodology"]["risk_score_created"] is False
def test_country_profile_and_unconfigured_state(monkeypatch):
    monkeypatch.setattr(module,"_core_json",fake_core);profile=module.build_country_profile(settings(),country="KEN")
    assert profile["counts"]["records"]==3 and "not a resource-security score" in profile["boundary"]
    empty=module.build_records(settings(platform_core_enabled=False,platform_core_url=""))
    assert empty["records"]==[] and empty["integration"]["state"]=="core-unconfigured"
def test_public_routes(monkeypatch):
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_ENABLED","true");monkeypatch.setenv("SC_SI_PLATFORM_CORE_URL","https://core.example.test");monkeypatch.setenv("SC_SI_PLATFORM_CORE_PUBLIC_API_KEY","test-public-key")
    from app.config import get_settings;get_settings.cache_clear();monkeypatch.setattr(module,"_core_json",fake_core)
    urls=["/public/trade-energy-resources","/public/trade-energy-resources/records","/public/trade-energy-resources/facets","/public/trade-energy-resources/trade","/public/trade-energy-resources/energy","/public/trade-energy-resources/resources","/public/trade-energy-resources/dependencies?geography_code=KEN","/public/trade-energy-resources/country-profile?country=KEN","/public/trade-energy-resources/brief?geography_code=KEN","/public/trade-energy-resources/diagnostics"]
    assert all(client.get(u).status_code==200 for u in urls)
def test_interface_wordpress_and_release_contract():
    root=Path(__file__).resolve().parents[2];html=(root/'backend/public_app/index.html').read_text();js=(root/'backend/public_app/assets/resources-v260.js').read_text();css=(root/'backend/public_app/assets/resources-v260.css').read_text();app_js=(root/'backend/public_app/assets/app.js').read_text();php=(root/'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
    assert 'data-route="resources"' in html and 'id="resourceStudio"' in html
    assert 'SCResourcesV260' in js and '.resource-studio' in css
    assert 'const APP_VERSION="2.12.1"' in app_js
    assert 'Version: 2.12.1' in php and 'sc_trade_energy_resource_security_observatory' in php
    assert 'No proprietary security score' in html
