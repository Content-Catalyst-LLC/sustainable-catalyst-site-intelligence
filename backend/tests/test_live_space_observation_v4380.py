from pathlib import Path
from types import SimpleNamespace
import json

from fastapi.testclient import TestClient

from app.live_space_observation_v4380 import provider_catalog, readiness, search
from app.main import app

ROOT=Path(__file__).resolve().parents[2]
CLIENT=TestClient(app)
SETTINGS=SimpleNamespace(space_observation_timeout_seconds=7)


def test_space_provider_catalog_is_five_lane_public_and_credential_free():
    p=provider_catalog(SETTINGS)
    assert p['ok'] is True and p['version']=='4.39.0'
    assert p['provider_count']==5 and p['default_provider']=='astronomy-observations'
    ids=[r['id'] for r in p['providers']]
    assert ids==['planetary-imagery','astronomy-observations','solar-system-ephemeris','exoplanets','seti-archive']
    assert all(r['configured'] and not r['configuration_required'] for r in p['providers'])
    assert p['credential_required'] is False


def test_space_readiness_is_network_free_and_nonblocking():
    p=readiness(SETTINGS)
    assert p['ok'] is True
    assert p['network_calls_performed'] is False
    assert p['release_blocking_upstream_health'] is False
    assert all(p['checks'].values())


def test_planetary_stac_search_returns_real_asset_without_fabrication():
    calls=[]
    def fake_json(url,**kwargs):
        calls.append(url)
        if url.endswith('/collections'):
            return {'collections':[{'id':'moon-kaguya-dtm','title':'Moon Kaguya DTM','description':'Lunar analysis-ready collection'}]}
        return {'features':[{'id':'item-1','collection':'moon-kaguya-dtm','properties':{'title':'Kaguya DTM tile','datetime':'2025-01-01T00:00:00Z','platform':'Kaguya','instruments':['TC']},'assets':{'thumbnail':{'href':'https://stac.astrogeology.usgs.gov/previews/moon.png','roles':['thumbnail'],'type':'image/png'}}}]}
    p=search({'provider':'planetary-imagery','body':'moon','limit':4},SETTINGS,request_json=fake_json)
    assert p['ok'] is True and p['result_count']==1
    r=p['results'][0]
    assert r['record_type']=='planetary-stac-item'
    assert r['preview_url'].endswith('moon.png')
    assert r['body']=='moon'
    assert any('/collections' in u for u in calls) and any('/search?' in u for u in calls)


def test_mast_cone_search_normalizes_observation_records():
    class Result:
        charset='utf-8'
        body=json.dumps({'data':[{'obsid':'123','target_name':'M31','s_ra':10.68,'s_dec':41.27,'obs_collection':'HST','instrument_name':'ACS','filters':'F606W','t_min':59000.0,'dataRights':'PUBLIC'}]}).encode()
    def fake_bytes(url,**kwargs):
        assert url.endswith('/invoke')
        assert kwargs['method']=='POST'
        assert b'Mast.Caom.Cone' in kwargs['data']
        return Result()
    p=search({'provider':'astronomy-observations','target':'M31','limit':5},SETTINGS,request_bytes=fake_bytes)
    assert p['ok'] is True and p['result_count']==1
    r=p['results'][0]
    assert r['record_type']=='mast-observation' and r['metadata']['mission']=='HST'
    assert r['title']=='M31'


def test_jpl_horizons_search_returns_authoritative_ephemeris_excerpt():
    seen=[]
    def fake_json(url,**kwargs):
        seen.append(url)
        return {'signature':{'source':'NASA/JPL Horizons API'},'result':'JPL/HORIZONS\n$$SOE\n2026-Aug-16, RA, DEC\n$$EOE'}
    p=search({'provider':'solar-system-ephemeris','body':'mars','epoch':'2026-08-16T12:00:00Z'},SETTINGS,request_json=fake_json)
    assert p['ok'] is True and p['result_count']==1
    r=p['results'][0]
    assert r['record_type']=='jpl-horizons-ephemeris'
    assert 'JPL/HORIZONS' in r['metadata']['excerpt']
    assert 'COMMAND' in seen[0] and '499' in seen[0]


def test_exoplanet_tap_search_preserves_habitability_boundary():
    def fake_json(url,**kwargs):
        assert 'pscomppars' in url
        return [{'pl_name':'TRAPPIST-1 e','hostname':'TRAPPIST-1','discoverymethod':'Transit','disc_year':2017,'pl_orbper':6.1,'pl_rade':0.92,'pl_bmasse':0.69,'pl_eqt':251,'sy_dist':12.43}]
    p=search({'provider':'exoplanets','target':'TRAPPIST-1','limit':5},SETTINGS,request_json=fake_json)
    assert p['result_count']==1
    r=p['results'][0]
    assert r['title']=='TRAPPIST-1 e'
    assert r['metadata']['equilibrium_temperature_k']==251
    assert 'do not establish habitability' in r['truth']


def test_seti_archive_search_returns_public_archive_handoff_when_page_has_no_machine_rows():
    p=search({'provider':'seti-archive','target':'Proxima Centauri'},SETTINGS,request_text=lambda *a,**k:'<html><body>Open Data Archive</body></html>')
    assert p['ok'] is True and p['result_count']==1
    r=p['results'][0]
    assert r['record_type']=='seti-archive-search'
    assert 'not confirmation' in r['truth']


def test_provider_failure_degrades_only_that_request_and_does_not_block_release():
    def boom(*a,**k): raise RuntimeError('upstream unavailable')
    p=search({'provider':'exoplanets','target':'Kepler'},SETTINGS,request_json=boom)
    assert p['ok'] is False and p['state']=='degraded'
    assert p['result_count']==0 and p['upstream_failure_release_blocking'] is False


def test_public_space_readiness_and_provider_routes_are_live():
    providers=CLIENT.get('/public/space-observation/providers')
    ready=CLIENT.get('/public/space-observation/readiness')
    assert providers.status_code==200 and ready.status_code==200
    assert providers.json()['version']=='4.39.0'
    assert ready.json()['ok'] is True


def test_frontend_and_wordpress_include_live_space_and_iframe_repairs():
    js=(ROOT/'backend/public_app/assets/live-space-observation-v4380.js').read_text()
    css=(ROOT/'backend/public_app/assets/iframe-navigation-v4380.css').read_text()
    idx=(ROOT/'backend/public_app/index.html').read_text()
    assert 'const VERSION="4.39.0"' in js
    assert '/public/space-observation/search' in js
    assert '5 live acquisition lanes' in js
    assert 'minmax(214px,236px)' in css
    assert 'html.scsi-wordpress-fixed-embed' in css
    assert 'id="liveSpaceObservation"' in idx
    assert 'live-space-observation-v4380.js?v=4.39.0' in idx
    wp=ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'
    assert (wp/'live-space-observation-v4380.js').read_bytes()==(ROOT/'backend/public_app/assets/live-space-observation-v4380.js').read_bytes()
    assert (wp/'iframe-navigation-v4380.css').read_bytes()==(ROOT/'backend/public_app/assets/iframe-navigation-v4380.css').read_bytes()


def test_release_identity_and_deployment_gate_include_live_space():
    assert CLIENT.get('/public/build-info').json()['version']=='4.39.0'
    d=CLIENT.get('/public/deployment-verification').json()
    assert d['contract']=='deployment-verification-live-space-observation-v4380'
    assert d['checks']['live_space_observation_ready'] is True
    assert d['checks']['space_credential_free_core_ready'] is True
    assert '/public/space-observation/readiness' in d['required_routes']
