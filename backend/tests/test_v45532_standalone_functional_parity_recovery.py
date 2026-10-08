from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.standalone_functional_parity_v45532 import certification, manifest, routes
from app.version import APP_VERSION, RELEASE_NAME

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_release_identity_and_route_inventory():
    assert APP_VERSION == "4.56.0"
    assert RELEASE_NAME == "Standalone Production Consolidation & Certification"
    m = capability_manifest(app.routes)
    assert m["registry_version"] == "2.7.0"
    assert m["route_count"] == 1521
    assert m["modularized_route_count"] == 212
    assert m["capability_count"] == 32
    assert m["unclassified_route_count"] == 0
    family = next(x for x in m["capabilities"] if x["capability_id"] == "standalone-functional-parity")
    assert family["route_count"] == 3
    assert family["modularized_route_count"] == 3
    assert family["maturity"] == "production"
    keys=[(method,row["path"]) for row in route_inventory(app.routes) for method in row["methods"]]
    assert len(keys)==len(set(keys))


def test_parity_registry_and_contract():
    data=json.loads((ROOT/'backend/data/standalone_functional_parity_registry_v45532.json').read_text())
    assert data['version']==APP_VERSION
    assert data['authority']['wordpress_runtime_dependency'] is False
    assert len(data['required_workspaces']) >= 30
    assert data['certification']['http_200_is_not_functional_pass'] is True
    assert data['certification']['browser_interaction_required'] is True
    assert data['certification']['no_demo_records'] is True


def test_parity_http_contract_routes():
    for path in ['/public/web-app/parity','/public/web-app/parity/routes','/public/web-app/parity/certification']:
        response=client.get(path)
        assert response.status_code==200
        assert response.json()['version']==APP_VERSION
    assert manifest()['workspace_count'] >= 30
    assert 'economics' in routes()['required_workspaces']
    assert 'browser-history' in certification()['functional_controls']


def test_standalone_root_is_migrated_functional_application():
    html=(ROOT/'web/index.html').read_text()
    for token in ['id="primaryNavigation"','id="economicsStudio"','id="lawStudio"','id="scienceStudio"','id="humanitarianStudio"','id="resourceStudio"','id="spatialEvidenceStudio"']:
        assert token in html
    assert 'standalone-api-bridge-v45532.js' in html
    assert 'standalone-functional-parity-v45532.js' in html


def test_migrated_application_assets_are_present():
    assets=ROOT/'web/app/assets'
    required=['app.js','app.css','vector-cartography-v3230.js','economics-v220.js','law-v230.js','science-v240.js','humanitarian-v250.js','resources-v260.js','dossiers-v270.js','research-v2100.js','spatial-v2150.js','standalone-api-bridge-v45532.js','standalone-functional-parity-v45532.js']
    for name in required:
        assert (assets/name).is_file(), name
    assert len(list(assets.glob('*.js'))) >= 70


def test_standalone_bridge_rewrites_reliable_domain_routes():
    js=(ROOT/'web/app/assets/standalone-api-bridge-v45532.js').read_text()
    for old,new in [
        ('/public/economics-sustainability/records','/public/reliable/economics/records'),
        ('/public/international-law-observatory/records','/public/reliable/law/records'),
        ('/public/scientific-earth-systems/records','/public/reliable/science/records'),
        ('/public/humanitarian-conflict-displacement/records','/public/reliable/humanitarian/records'),
        ('/public/trade-energy-resources/records','/public/reliable/resources/records'),
        ('/public/intelligence-dossiers/country','/public/reliable/dossiers/country'),
    ]:
        assert old in js and new in js
    assert 'window.fetch=' in js
    assert 'XMLHttpRequest' in js


def test_deep_links_and_country_context_are_migrated_before_legacy_boot():
    js=(ROOT/'web/app/assets/standalone-api-bridge-v45532.js').read_text()
    for name in ['country','dossiers','economics','law','science','humanitarian','resources','events','research','earth']:
        assert f'{name}:"' in js
    assert 'q.set("country",country.toUpperCase())' in js
    assert 'history.replaceState' in js


def test_nginx_history_fallback_and_static_app_paths():
    conf=(ROOT/'web/nginx.conf').read_text()
    assert 'try_files $uri $uri/ /index.html' in conf
    assert 'location = /healthz' in conf
    assert 'Service-Worker-Allowed "/app/"' in conf


def test_no_demo_record_injection_in_parity_bridge():
    combined='\n'.join((ROOT/'web/app/assets'/n).read_text() for n in ['standalone-api-bridge-v45532.js','standalone-functional-parity-v45532.js'])
    assert 'mock record' not in combined.lower()
