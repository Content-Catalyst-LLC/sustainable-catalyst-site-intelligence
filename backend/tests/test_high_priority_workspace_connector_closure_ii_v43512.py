from fastapi.testclient import TestClient
from app.config import Settings
from app.main import app
from app.version import APP_VERSION
import app.authoritative_connectors_v43512 as c
from app.authoritative_api_audit_v43512 import closure_status, source_inventory
from app.authoritative_api_production_audit_v43512 import production_audit, closure_ledger

CLIENT=TestClient(app)

def test_release_and_catalog_contract():
    assert APP_VERSION=='4.35.14'
    s=Settings(_env_file=None,airnow_api_key='')
    cat=c.connector_catalog(s)
    assert cat['connector_count']==35
    assert cat['live_connector_count']==23
    assert cat['discovery_connector_count']==6
    assert cat['auth_required_connector_count']==6
    assert c.connector_readiness(s)['ok'] is True

def test_climate_and_atmosphere_registered_backlog_are_closed():
    s=Settings(_env_file=None,airnow_api_key='')
    cl=closure_status(s)
    assert cl['ok'] is True
    assert cl['workspaces']['climate']['registered_backlog']==0
    assert cl['workspaces']['atmosphere']['registered_backlog']==0
    assert cl['climate_operational_without_credentials'] is True
    assert cl['atmosphere_discovery_without_credentials'] is True

def test_machine_readable_audit_counts_reconcile():
    s=Settings(_env_file=None,airnow_api_key='')
    a=production_audit(s)
    assert a['production_controls_ready'] is True
    assert a['machine_readable_summary']['registrations']==106
    assert a['machine_readable_summary']['counts']['LIVE']==43
    assert a['machine_readable_summary']['counts']['DISCOVERY']==10
    assert a['machine_readable_summary']['counts']['AUTH_REQUIRED']==14
    assert a['machine_readable_summary']['registered_not_retrieved']==35
    assert closure_ledger(s)['summary']['registered_not_retrieved']==35

def test_airnow_is_configuration_required_without_key():
    d=c.airnow_current(Settings(_env_file=None,airnow_api_key=''),latitude=41.8781,longitude=-87.6298)
    assert d['ok'] is False and d['configuration_required'] is True
    assert d['configuration_key']=='SC_SI_AIRNOW_API_KEY'
    assert d['network_calls_performed'] is False

def test_airnow_live_payload_is_bounded_and_preliminary(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:[
        {'DateObserved':'2026-08-11','HourObserved':16,'LocalTimeZone':'CST','ReportingArea':'Chicago','StateCode':'IL','Latitude':41.9,'Longitude':-87.6,'ParameterName':'PM2.5','AQI':57,'Category':{'Number':2,'Name':'Moderate'},'Extra':'drop'}
    ])
    d=c.airnow_current(Settings(_env_file=None,airnow_api_key='secret'),latitude=41.8781,longitude=-87.6298,distance_miles=25)
    assert d['ok'] and d['record_count']==1
    assert d['data'][0]['AQI']==57 and 'Extra' not in d['data'][0]
    assert 'secret' not in d['provenance']['endpoint']
    assert d['provenance']['data_status']=='preliminary-subject-to-change'

def test_airnow_bounds():
    s=Settings(_env_file=None,airnow_api_key='secret')
    for kw in ({'latitude':91,'longitude':0},{'latitude':0,'longitude':181},{'latitude':0,'longitude':0,'distance_miles':251}):
        try: c.airnow_current(s,**kw)
        except ValueError: pass
        else: raise AssertionError('expected ValueError')

def test_era5_catalogue_is_discovery_not_observation(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:{'id':'reanalysis-era5-single-levels','title':'ERA5 hourly data on single levels','extent':{'temporal':{}},'license':'other','links':[{'rel':'self'}]})
    d=c.era5_catalogue(Settings(_env_file=None))
    assert d['ok'] and d['mode']=='DISCOVERY'
    assert d['collection_id']=='reanalysis-era5-single-levels'
    assert 'reanalysis' in d['boundary'].lower()

def test_era5_collection_allowlist():
    try: c.era5_catalogue(Settings(_env_file=None),collection_id='everything')
    except ValueError: pass
    else: raise AssertionError('expected ValueError')

def test_cams_catalogue_is_discovery_not_ground_monitor(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:{'id':'cams-global-atmospheric-composition-forecasts','title':'CAMS forecasts','keywords':['atmosphere']})
    d=c.cams_catalogue(Settings(_env_file=None))
    assert d['ok'] and d['mode']=='DISCOVERY'
    assert 'ground-monitor' in d['boundary']

def test_audit_classifies_specific_sources_honestly():
    rows=source_inventory(Settings(_env_file=None,airnow_api_key=''))
    by={(r['workspace'],r['source_id']):r for r in rows}
    assert by[('Atmosphere, Air Quality & Aerosols','airnow')]['access_class']=='AUTH_REQUIRED'
    assert by[('Climate Baselines, Anomalies & Extremes','copernicus-era5')]['access_class']=='DISCOVERY'
    cams=by[('Atmosphere, Air Quality & Aerosols','cams-global')]
    assert cams['access_class']=='DISCOVERY' and cams['machine_readable'] is True

def test_new_routes_exist_and_return_config_or_mock_free_catalogue_shape():
    r=CLIENT.get('/public/atmosphere/live/airnow',params={'latitude':41.8781,'longitude':-87.6298})
    assert r.status_code==200 and r.json()['configuration_required'] is True
    for route in ('/public/authoritative-connectors','/public/authoritative-connectors/readiness','/public/authoritative-apis/production-readiness'):
        rr=CLIENT.get(route); assert rr.status_code==200

def test_external_health_remains_non_blocking():
    a=production_audit(Settings(_env_file=None,airnow_api_key=''))
    assert a['checks']['external_source_health_not_used_as_release_blocker'] is True
    assert a['network_calls_performed'] is False
