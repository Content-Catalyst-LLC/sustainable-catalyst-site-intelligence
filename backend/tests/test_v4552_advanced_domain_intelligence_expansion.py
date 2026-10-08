from pathlib import Path

from fastapi.testclient import TestClient

from app.advanced_domain_intelligence_v4552 import analyze, domain_profile, parity_audit, research_packet, registry_manifest
from app.main import app
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.version import APP_VERSION, RELEASE_NAME

client = TestClient(app)
DOMAINS = ["dossiers", "economics", "international-law", "science", "humanitarian", "resources"]


def root(): return Path(__file__).resolve().parents[2]


def test_release_identity():
    assert APP_VERSION == "4.55.3.2.2"
    assert RELEASE_NAME == "Browser API Transport & CORS Repair"


def test_registry_has_six_advanced_domains():
    r = registry_manifest()
    assert r["version"] == "4.55.3.2.2"
    assert len(r["domains"]) == 6
    assert {x["domain_id"] for x in r["domains"]} == set(DOMAINS)
    for d in r["domains"]:
        assert len(d["analysis_modes"]) >= 5
        assert len(d["research_workflow"]) >= 6
        assert len(d["recommended_handoffs"]) >= 4


def test_parity_gate_is_advanced_for_all_six():
    p = parity_audit()
    assert p["ok"] is True
    assert all(x["advanced"] for x in p["domains"])
    assert all(x["capability_count"] >= 10 for x in p["domains"])


def test_profiles_resolve():
    for domain in DOMAINS:
        assert domain_profile(domain)["workspace_level"] == "advanced-intelligence-workspace"


def test_domain_analyzers_are_deterministic_and_preserve_boundaries():
    fixtures = {
        "dossiers": [{"title":"Case A","record_type":"event","source_id":"src","date":"2026-01-01","actors":["Org A"]}],
        "economics": [{"indicator_code":"GDP","geography_code":"USA","period":"2024","value_number":100,"unit":"USD","frequency":"annual","source_id":"src"},{"indicator_code":"GDP","geography_code":"USA","period":"2025","value_number":110,"unit":"USD","frequency":"annual","source_id":"src"}],
        "international-law": [{"title":"Instrument","authority_level":"binding-treaty","legal_body":"UN","countries":["USA"],"subjects":["climate"],"display_date":"2025-01-01","source_id":"src"}],
        "science": [{"discipline":"ocean","mission":"mission-a","instrument":"sensor-a","target":"ocean","variable":"sst","value":22.1,"source_id":"src"}],
        "humanitarian": [{"event_type":"displacement","country":"SDN","actors":["Agency"],"displaced":1200,"source_id":"src"}],
        "resources": [{"family":"trade","geography_code":"USA","counterpart_code":"CAN","commodity":"electricity","value_number":50,"source_id":"src"}],
    }
    for domain, records in fixtures.items():
        a = analyze(domain, {"records":records})["result"]
        b = analyze(domain, {"records":records})["result"]
        assert a["analysis_digest"] == b["analysis_digest"]
        assert a["provenance"]["source_records_mutated"] is False
        assert a["provenance"]["missing_values_fabricated"] is False
        assert a["provenance"]["automatic_causality"] is False


def test_research_packets_are_content_addressed_and_no_auto_delivery():
    for domain in DOMAINS:
        p1 = research_packet(domain, {"records":[],"title":"Test"})["packet"]
        p2 = research_packet(domain, {"records":[],"title":"Test"})["packet"]
        assert p1["packet_digest"] == p2["packet_digest"]
        assert p1["packet_id"] == p2["packet_id"]
        assert p1["automatic_delivery"] is False
        assert p1["human_confirmation_required"] is True


def test_21_new_modular_routes_and_inventory():
    m = capability_manifest(app.routes)
    assert m["registry_version"] == "2.6.2"
    assert m["route_count"] == 1518
    assert m["modularized_route_count"] == 209
    assert m["capability_count"] == 31
    assert m["unclassified_route_count"] == 0
    family = next(x for x in m["capabilities"] if x["capability_id"] == "advanced-domain-intelligence")
    assert family["route_count"] == 21
    assert family["modularized_route_count"] == 21
    keys=[(method,row["path"]) for row in route_inventory(app.routes) for method in row["methods"]]
    assert len(keys) == len(set(keys))


def test_http_profiles_analysis_and_packets():
    for domain in DOMAINS:
        r = client.get(f"/public/domain-intelligence/{domain}/profile")
        assert r.status_code == 200 and r.json()["ok"] is True
        r = client.post(f"/public/domain-intelligence/{domain}/analyze", json={"records":[]})
        assert r.status_code == 200 and r.json()["result"]["domain"] == domain
        r = client.post(f"/public/domain-intelligence/{domain}/packet", json={"records":[]})
        assert r.status_code == 200 and r.json()["packet"]["domain"] == domain


def test_browser_expansion_is_loaded_and_uses_current_workspace_records():
    r = root()
    js = (r/"backend/public_app/assets/advanced-domain-intelligence-v4552.js").read_text()
    css = (r/"backend/public_app/assets/advanced-domain-intelligence-v4552.css").read_text()
    index = (r/"backend/public_app/index.html").read_text()
    sw = (r/"backend/public_app/service-worker.js").read_text()
    assert 'const VERSION="4.55.3.2.2"' in js
    for route in ["dossiers","economics","law","science","humanitarian","resources"]:
        assert route in js
    assert "Analyze current records" in js
    assert "Build research packet" in js
    assert "advanced-domain-intelligence-v4552.js?v=4.55.3.2.2" in index
    assert "advanced-domain-intelligence-v4552.css?v=4.55.3.2.2" in index
    assert "advanced-domain-intelligence-v4552.js" in sw
    assert ".advanced-domain-intelligence-v4552" in css


def test_existing_controllers_expose_current_records_for_analysis():
    assets = root()/"backend/public_app/assets"
    for name in ["economics-v220.js","law-v230.js","science-v240.js","humanitarian-v250.js","resources-v260.js"]:
        text=(assets/name).read_text()
        assert "records" in text and "status" in text
    assert "records: state.records" in (assets/"economics-v220.js").read_text()
    assert "records:state.records" in (assets/"law-v230.js").read_text()
    assert "records:state.records" in (assets/"science-v240.js").read_text()


def test_wordpress_stays_thin_shell():
    php=(root()/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert "Version: 4.55.3.2.2" in php
    assert "const VERSION = '4.55.3.2.2';" in php
    assert "const RELEASE_ID = 'site-intelligence-v4.55.3.2.2';" in php
    assert "const WORDPRESS_ROLE = 'public-site-launch-bridge';" in php
