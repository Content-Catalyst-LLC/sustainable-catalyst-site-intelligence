from fastapi.testclient import TestClient
from app.config import Settings
from app.main import app
from app.version import APP_VERSION
import app.authoritative_connectors_v43513 as c
from app.authoritative_api_audit_v43513 import closure_status, source_inventory
from app.authoritative_api_production_audit_v43513 import production_audit, closure_ledger

CLIENT=TestClient(app)

def test_release_and_catalog_contract():
    assert APP_VERSION=='4.35.13'
    s=Settings(_env_file=None)
    cat=c.connector_catalog(s)
    assert cat['connector_count']==40
    assert cat['live_connector_count']==26
    assert cat['discovery_connector_count']==8
    assert cat['auth_required_connector_count']==6
    assert c.connector_readiness(s)['ok'] is True

def test_water_and_hydrology_registered_backlogs_are_closed():
    cl=closure_status(Settings(_env_file=None))
    assert cl['ok'] is True
    assert cl['workspaces']['hydrology']['registered_backlog']==0
    assert cl['workspaces']['water_sanitation']['registered_backlog']==0
    assert cl['hydrology_live_without_credentials'] is True
    assert cl['water_sanitation_live_without_credentials'] is True

def test_machine_readable_audit_counts_reconcile():
    s=Settings(_env_file=None); a=production_audit(s)
    assert a['production_controls_ready'] is True
    assert a['machine_readable_summary']['registrations']==108
    assert a['machine_readable_summary']['counts']['LIVE']==46
    assert a['machine_readable_summary']['counts']['DISCOVERY']==12
    assert a['machine_readable_summary']['counts']['AUTH_REQUIRED']==14
    assert a['machine_readable_summary']['counts']['BULK']==2
    assert a['machine_readable_summary']['registered_not_retrieved']==34
    assert closure_ledger(s)['summary']['registered_not_retrieved']==34

def test_osm_water_is_bounded_and_supplemental(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:{'elements':[{'type':'node','id':1,'tags':{'man_made':'water_works'}}]})
    d=c.osm_water(Settings(_env_file=None),latitude=41.8781,longitude=-87.6298,radius_km=5)
    assert d['ok'] and d['record_count']==1 and d['mode']=='LIVE'
    assert 'supplemental' in d['boundary'].lower()
    try: c.osm_water(Settings(_env_file=None),latitude=0,longitude=0,radius_km=51)
    except ValueError: pass
    else: raise AssertionError('expected ValueError')

def test_sdwis_is_bounded_and_not_tap_water_safety(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:[{'PWSID':'IL0000001','PWSNAME':'Example','STATE':'IL'}])
    d=c.epa_sdwis(Settings(_env_file=None),dataset='county-served',filter_column='STATE',filter_value='IL',limit=25)
    assert d['ok'] and d['record_count']==1 and d['mode']=='LIVE'
    assert 'tap-water' in d['boundary']
    assert '/STATE/IL/' in d['provenance']['endpoint']
    try: c.epa_sdwis(Settings(_env_file=None),dataset='county-served',filter_column='BAD_COLUMN',filter_value='IL')
    except ValueError: pass
    else: raise AssertionError('expected ValueError')

def test_nidis_public_file_path_is_bounded(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:{'valid':'2026-08-11','features':[]})
    d=c.nidis_drought_file(Settings(_env_file=None),relative_path='usdm/example.geojson')
    assert d['ok'] and d['mode']=='LIVE'
    assert d['provenance']['endpoint'].startswith('https://storage.googleapis.com/noaa-nidis-drought-gov-data/')
    for bad in ('../secret.json','bad.txt',''):
        try: c.nidis_drought_file(Settings(_env_file=None),relative_path=bad)
        except ValueError: pass
        else: raise AssertionError('expected ValueError')

def test_nasa_gpm_is_discovery_not_precipitation_observation(monkeypatch):
    monkeypatch.setattr(c.prior,'nasa_cmr_collections',lambda settings,**kw:{'ok':True,'mode':'DISCOVERY','collections':[{'id':'GPM_3IMERGHH'}],'collection_count':1,'query':kw})
    d=c.nasa_gpm_imerg_discovery(Settings(_env_file=None),limit=5)
    assert d['ok'] and d['connector_id']=='nasa-gpm-imerg-cmr'
    assert d['mode']=='DISCOVERY' and 'not precipitation observations' in d['boundary']

def test_glofas_layer_api_is_discovery_not_warning(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:{'supported_layers':[{'name':'river_discharge','url':'https://example.invalid/{date}'}]})
    d=c.glofas_layers(Settings(_env_file=None))
    assert d['ok'] and d['layer_count']==1 and d['mode']=='DISCOVERY'
    assert 'official local flood warning' in d['boundary']

def test_audit_classifies_specific_sources_honestly():
    rows=source_inventory(Settings(_env_file=None)); by={(r['workspace'],r['source_id']):r for r in rows}
    assert by[('Water, Wastewater & Sanitation','openstreetmap-water-infrastructure')]['access_class']=='LIVE'
    assert by[('Water, Wastewater & Sanitation','epa-sdwis-drinking-water')]['access_class']=='LIVE'
    assert by[('Hydrology, Rivers, Flood & Drought','drought-gov')]['access_class']=='LIVE'
    assert by[('Hydrology, Rivers, Flood & Drought','nasa-gpm-imerg')]['access_class']=='DISCOVERY'
    assert by[('Hydrology, Rivers, Flood & Drought','copernicus-glofas')]['access_class']=='DISCOVERY'

def test_new_routes_are_registered():
    paths={getattr(r,'path',None) for r in app.routes}
    for route in ('/public/water-sanitation/live/osm-water','/public/water-sanitation/live/epa-sdwis','/public/hydrology/live/drought-gov','/public/hydrology/discovery/nasa-gpm','/public/hydrology/discovery/glofas'):
        assert route in paths

def test_existing_public_control_routes_still_work():
    for route in ('/public/authoritative-connectors','/public/authoritative-connectors/readiness','/public/authoritative-apis/production-readiness'):
        r=CLIENT.get(route); assert r.status_code==200

def test_external_health_remains_non_blocking():
    a=production_audit(Settings(_env_file=None))
    assert a['checks']['external_source_health_not_used_as_release_blocker'] is True
    assert a['network_calls_performed'] is False
