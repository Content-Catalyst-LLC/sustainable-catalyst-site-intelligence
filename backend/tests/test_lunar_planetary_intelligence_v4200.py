from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.planetary_intelligence_v4200 import catalog, state, readiness
CLIENT=TestClient(app); ROOT=Path(__file__).resolve().parents[2]

def test_overview_preserves_v4_route_architecture():
    p=CLIENT.get('/public/planetary-intelligence').json()
    assert p['ok'] and p['version']=='4.36.0' and p['route']=='earth' and p['destinations']==['moon','mars']
    assert len(p['contract_sha256'])==64
    assert CLIENT.get('/public/v4/navigation').json()['route_count']==35

def test_catalog_has_authoritative_moon_and_mars_products():
    p=catalog(); assert p['body_count']==2 and p['product_count']>=7
    assert {'moon','mars'}=={x['body_id'] for x in p['products']}
    assert all('usgs.gov' in x['source_url'] for x in p['products'])
    assert all(x['nasa_trek_url'].startswith('https://trek.nasa.gov/') for x in p['products'])

def test_planetary_state_does_not_substitute_local_texture_for_mission_imagery():
    p=state('moon','lro-wac-morphology',10,20,4)
    assert p['observation']['mission']=='Lunar Reconnaissance Orbiter'
    assert p['observation']['embedded_verified_raster'] is False
    assert p['truth']['local_surface_texture_is_mission_imagery'] is False
    assert p['truth']['official_source_handoff_available'] is True
    assert len(p['state_sha256'])==64

def test_mars_themis_quantitative_boundary_is_explicit():
    p=state('mars','themis-controlled',0,137.4,3)
    assert 'qualitative' in p['observation']['product_type']
    assert '8-bit' in p['observation']['quantitative_use']
    assert p['view']['not_earth_coordinates'] is True

def test_unknown_body_fails_explicitly():
    p=CLIENT.get('/public/planetary-intelligence/body/venus').json()
    assert p['ok'] is False and set(p['supported_bodies'])=={'moon','mars'}

def test_export_and_readiness():
    p=CLIENT.get('/public/planetary-intelligence/export-manifest',params={'body':'mars','product':'ctx-dtm'}).json()
    assert p['schema']=='sc-site-intelligence-planetary-view/1.0'
    assert p['review']['mission_imagery_fabricated'] is False
    assert len(p['manifest_sha256'])==64
    r=readiness(); assert r['ok'] and r['summary']['bodies']==2 and r['summary']['products']>=7

def test_assets_ship_in_app_service_worker_and_wordpress():
    html=(ROOT/'backend/public_app/index.html').read_text(); sw=(ROOT/'backend/public_app/service-worker.js').read_text()
    js=(ROOT/'backend/public_app/assets/planetary-intelligence-v4200.js').read_text(); css=(ROOT/'backend/public_app/assets/planetary-intelligence-v4200.css').read_text()
    assert 'data-scsi-planetary-contract="planetary-intelligence-v4200"' in html
    assert 'id="earthPlanetaryEnter"' in html
    assert 'planetary-intelligence-v4200.js' in sw and 'planetary-intelligence-v4200.css' in sw
    assert 'SCSIPlanetaryV4200' in js and '.planetary-stage' in css
    assert js==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/planetary-intelligence-v4200.js').read_text()
    assert css==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/planetary-intelligence-v4200.css').read_text()
