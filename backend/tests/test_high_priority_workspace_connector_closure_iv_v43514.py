from fastapi.testclient import TestClient
from app.config import Settings
from app.main import app
from app.version import APP_VERSION
import app.authoritative_connectors_v43514 as c
from app.authoritative_api_audit_v43514 import closure_status, source_inventory
from app.authoritative_api_production_audit_v43514 import production_audit, closure_ledger

CLIENT=TestClient(app)

def settings(**kw): return Settings(_env_file=None, **kw)

def test_release_and_catalog_contract():
    assert APP_VERSION=='4.35.25'
    cat=c.connector_catalog(settings())
    assert cat['connector_count']==45
    assert cat['live_connector_count']==28
    assert cat['discovery_connector_count']==9
    assert cat['auth_required_connector_count']==8
    assert c.connector_readiness(settings())['ok'] is True

def test_agriculture_and_humanitarian_registered_backlogs_are_closed():
    cl=closure_status(settings())
    assert cl['ok'] is True
    assert cl['workspaces']['agriculture_food_security']['registered_backlog']==0
    assert cl['workspaces']['humanitarian']['registered_backlog']==0
    assert cl['agriculture_live_without_credentials'] is True
    assert cl['humanitarian_live_without_credentials'] is True

def test_machine_readable_audit_counts_reconcile():
    a=production_audit(settings())
    assert a['production_controls_ready'] is True
    assert a['machine_readable_summary']['registrations']==112
    assert a['machine_readable_summary']['counts']['LIVE']==48
    assert a['machine_readable_summary']['counts']['DISCOVERY']==13
    assert a['machine_readable_summary']['counts']['AUTH_REQUIRED']==17
    assert a['machine_readable_summary']['counts']['BULK']==2
    assert a['machine_readable_summary']['registered_not_retrieved']==32
    assert closure_ledger(settings())['summary']['registered_not_retrieved']==32

def test_gdacs_is_bounded_live_and_not_an_emergency_service(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:{'features':[{'eventid':1,'alertlevel':'Orange'}]})
    d=c.gdacs_events(settings(),event_type='EQ',alert_level='orange',limit=25)
    assert d['ok'] and d['mode']=='LIVE'
    assert 'eventtype=EQ' in d['provenance']['endpoint'] and 'alertlevel=orange' in d['provenance']['endpoint']
    assert 'national warning authorities' in d['boundary']
    try: c.gdacs_events(settings(),event_type='BAD')
    except ValueError: pass
    else: raise AssertionError('expected ValueError')

def test_hdx_ckan_is_discovery_not_humanitarian_condition(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:{'success':True,'result':{'count':1,'results':[{'name':'x'}]}})
    d=c.hdx_dataset_search(settings(),query='food security somalia',rows=10)
    assert d['ok'] and d['mode']=='DISCOVERY'
    assert 'package_search' in d['provenance']['endpoint']
    assert 'not a verified current humanitarian condition' in d['boundary']

def test_hdx_hapi_requires_app_identifier_and_redacts_it(monkeypatch):
    d=c.hdx_hapi(settings(),dataset='food-security',location_code='SOM')
    assert not d['ok'] and d['configuration_key']=='SC_SI_HDX_HAPI_APP_IDENTIFIER'
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:{'data':[{'location_code':'SOM','ipc_phase':'3'}]})
    d=c.hdx_hapi(settings(hdx_hapi_app_identifier='test-app-id'),dataset='food-security',location_code='SOM',limit=25)
    assert d['ok'] and d['mode']=='AUTH_REQUIRED'
    assert 'test-app-id' not in d['provenance']['endpoint'] and 'REDACTED' in d['provenance']['endpoint']
    assert 'not a new Site Intelligence classification' in d['boundary']

def test_ipc_requires_key_and_preserves_classification_authority(monkeypatch):
    d=c.ipc_food_security(settings(),resource='country',country='SO')
    assert not d['ok'] and d['configuration_key']=='SC_SI_IPC_API_KEY'
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:[{'country':'SO','phase3plus':123}])
    d=c.ipc_food_security(settings(ipc_api_key='secret'),resource='country',country='SO',year=2026,analysis_type='A')
    assert d['ok'] and d['mode']=='AUTH_REQUIRED'
    assert 'secret' not in d['provenance']['endpoint'] and 'REDACTED' in d['provenance']['endpoint']
    assert 'does not create' in d['boundary']

def test_fews_net_public_path_is_bounded_and_scenario_aware(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:{'count':1,'results':[{'country_code':'SO','scenario':'CS'}]})
    d=c.fews_net_data(settings(),dataset='food-security-phase',country_code='SO',scenario='CS',page_size=25)
    assert d['ok'] and d['mode']=='LIVE'
    assert 'country_code=SO' in d['provenance']['endpoint'] and 'scenario=CS' in d['provenance']['endpoint']
    assert 'Projections are not observations' in d['boundary']
    try: c.fews_net_data(settings(),dataset='food-security-phase')
    except ValueError: pass
    else: raise AssertionError('expected ValueError')

def test_audit_classifies_specific_sources_honestly():
    rows=source_inventory(settings()); by={(r['workspace'],r['source_id']):r for r in rows}
    assert by[('Humanitarian Intelligence','gdacs')]['access_class']=='LIVE'
    assert by[('Sources & Methodology','reliefweb')]['access_class']=='AUTH_REQUIRED'
    assert by[('Conflict & Human Security','hdx')]['access_class']=='DISCOVERY'
    assert by[('Agriculture, Crops & Food Systems','fews-net-data-platform')]['access_class']=='LIVE'
    assert by[('Agriculture, Crops & Food Systems','ipc-food-security-api')]['access_class']=='AUTH_REQUIRED'
    assert by[('Humanitarian Intelligence','hdx-hapi-food-security')]['access_class']=='AUTH_REQUIRED'

def test_new_routes_are_registered():
    paths={getattr(r,'path',None) for r in app.routes}
    for route in ('/public/humanitarian/live/gdacs','/public/humanitarian/discovery/hdx','/public/food-security/live/hdx-hapi','/public/food-security/live/ipc','/public/food-security/live/fews-net'):
        assert route in paths

def test_readiness_is_network_free():
    r=c.connector_readiness(settings())
    assert r['ok'] is True and r['network_calls_performed'] is False

def test_external_health_remains_non_blocking():
    a=production_audit(settings())
    assert a['checks']['external_source_health_not_used_as_release_blocker'] is True
    assert a['network_calls_performed'] is False

def test_existing_public_control_routes_still_work():
    for route in ('/public/authoritative-connectors','/public/authoritative-connectors/readiness','/public/authoritative-apis/production-readiness','/public/evidence-intelligence/readiness','/public/workspace-evidence/readiness'):
        r=CLIENT.get(route); assert r.status_code==200

def test_food_security_semantic_boundaries_remain_distinct():
    texts=' '.join(x['boundary'] for x in c.NEW_CONNECTORS)
    assert 'Projections are not observations' in texts
    assert 'not a new Site Intelligence classification' in texts
    assert 'does not create, upgrade, downgrade' in texts
