from fastapi.testclient import TestClient
from app.config import Settings
from app.main import app
from app.version import APP_VERSION
import app.authoritative_connectors_v43515 as c
from app.authoritative_api_audit_v43515 import closure_status, source_inventory
from app.authoritative_api_production_audit_v43515 import production_audit, closure_ledger

CLIENT=TestClient(app)
def settings(**kw): return Settings(_env_file=None, **kw)

def test_release_and_catalog_contract():
    assert APP_VERSION=='4.36.1'
    cat=c.connector_catalog(settings())
    assert cat['connector_count']==50 and cat['live_connector_count']==31
    assert cat['discovery_connector_count']==11 and cat['auth_required_connector_count']==8
    assert c.connector_readiness(settings())['ok'] is True

def test_target_registered_backlogs_are_closed():
    cl=closure_status(settings())
    assert cl['ok'] is True
    assert cl['workspaces']['mining_critical_materials']['registered_backlog']==0
    assert cl['workspaces']['industrial_manufacturing_trade']['registered_backlog']==0
    assert cl['mining_live_without_credentials'] and cl['industrial_live_without_credentials']

def test_machine_readable_counts_reconcile():
    a=production_audit(settings())
    assert a['production_controls_ready'] is True
    assert a['machine_readable_summary']['registrations']==112
    counts=a['machine_readable_summary']['counts']
    assert counts['LIVE']==51 and counts['DISCOVERY']==15 and counts['AUTH_REQUIRED']==17
    assert counts['BULK']==2 and counts['STALE']==0
    assert a['machine_readable_summary']['registered_not_retrieved']==27
    assert closure_ledger(settings())['summary']['registered_not_retrieved']==27

def test_osm_mining_is_bounded_supplemental_live(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:{'elements':[{'type':'node','id':1,'tags':{'landuse':'quarry'}}]})
    d=c.osm_mining(settings(),latitude=40,longitude=-105,radius_km=5)
    assert d['ok'] and d['mode']=='LIVE' and d['record_count']==1
    assert 'around%3A5000' in d['provenance']['endpoint']
    assert 'do not establish ownership' in d['boundary']
    try: c.osm_mining(settings(),latitude=40,longitude=-105,radius_km=60)
    except ValueError: pass
    else: raise AssertionError('expected ValueError')

def test_usmin_is_discovery_not_live_mine_telemetry(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:{'id':'USGS:6464de5bd34ec179a83d9e6c','title':'USMIN'})
    d=c.usgs_usmin_discovery(settings())
    assert d['ok'] and d['mode']=='DISCOVERY'
    assert '/datacatalog/api/search/USGS%3A6464de5bd34ec179a83d9e6c' in d['provenance']['endpoint']
    assert 'not live mine operations' in d['boundary']

def test_mcs_is_discovery_and_preserves_annual_scope(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:{'title':'Mineral Commodity Summaries 2026'})
    d=c.usgs_mcs_2026_discovery(settings())
    assert d['ok'] and d['mode']=='DISCOVERY'
    assert '2021–2025' in d['boundary'] and 'not mine-level telemetry' in d['boundary']

def test_osm_industrial_is_bounded_live(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:{'elements':[{'type':'way','id':2,'tags':{'man_made':'works'}}]})
    d=c.osm_industrial(settings(),latitude=41.88,longitude=-87.63,radius_km=8)
    assert d['ok'] and d['mode']=='LIVE' and d['record_count']==1
    assert 'current operation' in d['boundary']

def test_wits_is_bounded_trade_statistics(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,timeout=8:{'dataset':[{'OBS_VALUE':1}]})
    d=c.wits_trade_stats(settings(),reporter='usa',year=2024,partner='wld',product='fuels',indicator='XPRT-TRD-VL')
    assert d['ok'] and d['mode']=='LIVE'
    assert '/reporter/usa/year/2024/partner/wld/product/fuels/indicator/XPRT-TRD-VL' in d['provenance']['endpoint']
    assert 'not shipment telemetry' in d['boundary']
    try: c.wits_trade_stats(settings(),reporter='all',year=2024)
    except ValueError: pass
    else: raise AssertionError('expected ValueError')

def test_source_inventory_reclassifies_only_specific_registered_gaps():
    by={(r['workspace'],r['source_id']):r for r in source_inventory(settings())}
    assert by[('Mining & Critical Materials','openstreetmap-mining')]['access_class']=='LIVE'
    assert by[('Mining & Critical Materials','usgs-usmin')]['access_class']=='DISCOVERY'
    assert by[('Mining & Critical Materials','usgs-mcs-2026')]['access_class']=='DISCOVERY'
    assert by[('Industrial Manufacturing & Trade','openstreetmap-industrial')]['access_class']=='LIVE'
    assert by[('Industrial Manufacturing & Trade','world-bank-wits-trade')]['access_class']=='LIVE'

def test_new_routes_are_registered():
    paths={getattr(r,'path',None) for r in app.routes}
    for route in ('/public/mining-critical-materials/live/osm-mining','/public/mining-critical-materials/discovery/usgs-usmin','/public/mining-critical-materials/discovery/usgs-mcs-2026','/public/industrial-manufacturing/live/osm-industrial','/public/industrial-manufacturing/live/wits'):
        assert route in paths

def test_readiness_is_network_free_and_external_health_nonblocking():
    r=c.connector_readiness(settings()); assert r['ok'] and r['network_calls_performed'] is False
    a=production_audit(settings()); assert a['checks']['external_source_health_not_used_as_release_blocker'] is True and a['network_calls_performed'] is False

def test_existing_public_control_routes_still_work():
    for route in ('/public/authoritative-connectors','/public/authoritative-connectors/readiness','/public/authoritative-apis/production-readiness','/public/evidence-intelligence/readiness','/public/workspace-evidence/readiness'):
        r=CLIENT.get(route); assert r.status_code==200

def test_semantic_boundaries_keep_discovery_and_statistics_distinct():
    text=' '.join(x['boundary'] for x in c.NEW_CONNECTORS)
    assert 'not live mine operations' in text
    assert 'not mine-level telemetry' in text
    assert 'not shipment telemetry' in text

def test_closure_ledger_reports_zero_target_registered_backlog():
    s=closure_ledger(settings())['summary']
    assert s['mining_registered_backlog']==0 and s['industrial_registered_backlog']==0
