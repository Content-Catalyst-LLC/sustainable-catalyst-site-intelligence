from pathlib import Path
from types import SimpleNamespace
from fastapi.testclient import TestClient
from app import humanitarian_conflict_displacement_observatory as module
from app.main import app

client=TestClient(app)

def settings(**overrides):
    values={"platform_core_enabled":True,"platform_core_url":"https://core.example.test","platform_core_public_api_key":"test-public-key","humanitarian_conflict_displacement_enabled":True,"humanitarian_conflict_displacement_timeout_seconds":9,"humanitarian_conflict_displacement_cache_ttl_seconds":90}
    values.update(overrides); return SimpleNamespace(**values)

def fake_core(config,path,query=None,**kwargs):
    if "international-law" in path:
        return {"data":[{"id":"law-1","source_id":"ohchr-uhri","record_type":"human_rights_recommendation","title":"Protection of displaced civilians","countries":["SDN"],"subjects":["Human rights","Displacement"],"publication_date":"2026-01-02","canonical_source_url":"https://example.test/law?api_key=hidden","metadata":{"token":"hidden","safe":"yes"},"attribution":"OHCHR"}]}
    if "economics" in path:
        return {"data":[{"id":"econ-1","source_id":"unhcr","record_type":"demographic_statistic","indicator_name":"Refugees under UNHCR mandate","geography_code":"SDN","period":"2025","value":1234,"unit":"people","source_url":"https://example.test/data?key=hidden"}]}
    return {"data":[{"id":"live-1","source_id":"ocha-hdx","domain":"humanitarian","metric":"Food insecurity assessment","title":"Food and water needs assessment","country_code":"SDN","observed_at":"2026-01-03","source_url":"https://example.test/live"}]}

def fake_events(**kwargs):
    return {"data_state":"live","source_states":{"reliefweb":"live"},"events":[{"id":"event-1","title":"Humanitarian situation report Sudan","summary":"Public report","category":"humanitarian","category_label":"Humanitarian reports","source":"reliefweb","source_name":"ReliefWeb","source_url":"https://reliefweb.int/report/example","observed_at":"2026-01-04","country_code":"SDN","coordinates":[30.2,15.5],"severity":"unknown","record_type":"reported-event","data_state":"live"}]}

def test_records_sanitize_and_preserve_distinctions(monkeypatch):
    monkeypatch.setattr(module,"_core_json",fake_core); monkeypatch.setattr(module,"unified_events",fake_events)
    payload=module.build_records(settings(),country="SDN",limit=20)
    assert payload["fallback_used"] is False
    assert {r["category"] for r in payload["records"]}>={"displacement","humanitarian","food-water-health","rights-protection"}
    assert "api_key" not in str(payload) and "test-public-key" not in str(payload) and "token" not in str(payload)
    assert any(r.get("geometry") for r in payload["records"])

def test_unconfigured_core_keeps_live_events_without_fabrication(monkeypatch):
    monkeypatch.setattr(module,"unified_events",fake_events)
    payload=module.build_records(settings(platform_core_enabled=False,platform_core_url=""),limit=20)
    assert len(payload["records"])==1
    assert payload["source_states"]["core"]=="unconfigured"
    assert payload["fallback_used"] is False

def test_country_profile_and_displacement(monkeypatch):
    monkeypatch.setattr(module,"_core_json",fake_core); monkeypatch.setattr(module,"unified_events",fake_events)
    profile=module.build_country_profile(settings(),country="SDN")
    displacement=module.build_displacement(settings(),country="SDN")
    assert profile["country"]=="SDN" and profile["counts"]["records"]>=3
    assert displacement["counts"]["records"]>=1
    assert "must not be added" in displacement["warning"]

def test_public_routes(monkeypatch):
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_ENABLED","true"); monkeypatch.setenv("SC_SI_PLATFORM_CORE_URL","https://core.example.test"); monkeypatch.setenv("SC_SI_PLATFORM_CORE_PUBLIC_API_KEY","test-public-key")
    from app.config import get_settings; get_settings.cache_clear()
    monkeypatch.setattr(module,"_core_json",fake_core); monkeypatch.setattr(module,"unified_events",fake_events)
    urls=["/public/humanitarian-conflict-displacement","/public/humanitarian-conflict-displacement/records?country=SDN","/public/humanitarian-conflict-displacement/facets","/public/humanitarian-conflict-displacement/timeline?country=SDN","/public/humanitarian-conflict-displacement/displacement?country=SDN","/public/humanitarian-conflict-displacement/country-profile?country=SDN","/public/humanitarian-conflict-displacement/access?country=SDN","/public/humanitarian-conflict-displacement/brief?country=SDN","/public/humanitarian-conflict-displacement/diagnostics"]
    responses=[client.get(u) for u in urls]
    assert all(r.status_code==200 for r in responses)
    assert responses[-1].json()["public_safety"]["military_targeting"] is False

def test_public_interface_wordpress_and_release_contract():
    root=Path(__file__).resolve().parents[2]
    html=(root/"backend/public_app/index.html").read_text(); js=(root/"backend/public_app/assets/humanitarian-v250.js").read_text(); css=(root/"backend/public_app/assets/humanitarian-v250.css").read_text(); app_js=(root/"backend/public_app/assets/app.js").read_text(); php=(root/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert 'data-route="humanitarian"' in html and 'id="humanitarianStudio"' in html
    assert "SCHumanitarianV250" in js and ".humanitarian-studio" in css
    assert 'const APP_VERSION="3.6.1"' in app_js
    assert "Version: 3.6.1" in php and "sc_humanitarian_conflict_displacement_observatory" in php
    assert "No fabricated crisis records" in html
