from fastapi.testclient import TestClient
import pytest
from app.config import Settings
from app.main import app
from app import authoritative_connectors_v43511 as c
from app.authoritative_api_audit_v43511 import source_inventory, closure_status, audit_readiness
from app.authoritative_api_production_audit_v43511 import production_audit

def settings(**kw): return Settings(_env_file=None,**kw)

def test_catalog_expands_to_32_and_readiness_network_free():
    x=c.connector_catalog(settings()); assert x['connector_count']==32 and x['live_connector_count']==23 and x['discovery_connector_count']==4 and x['auth_required_connector_count']==5
    r=c.connector_readiness(settings()); assert r['ok'] and r['network_calls_performed'] is False

def test_energy_and_digital_registered_backlog_zero():
    cl=closure_status(settings()); assert cl['ok']; assert cl['workspaces']['energy']['registered_backlog']==0; assert cl['workspaces']['digital']['registered_backlog']==0
    assert cl['energy_official_api_credentials_remaining']==3 and cl['digital_operational_without_credentials'] is True

def test_machine_backlog_drops_from_43_to_37():
    p=production_audit(settings()); assert p['production_controls_ready']; assert p['machine_readable_summary']['registrations']==105; assert p['machine_readable_summary']['registered_not_retrieved']==37
    assert p['machine_readable_summary']['counts']['LIVE']==43 and p['machine_readable_summary']['counts']['DISCOVERY']==8 and p['machine_readable_summary']['counts']['AUTH_REQUIRED']==13

def test_inventory_states_are_interface_specific():
    rows=source_inventory(settings()); m={(r['workspace'],r['source_id']):r for r in rows}
    assert m[('Energy Infrastructure & Power Systems','openstreetmap-power')]['access_class']=='LIVE'
    assert m[('Energy Infrastructure & Power Systems','ember-electricity-data')]['access_class']=='AUTH_REQUIRED'
    assert m[('Energy Infrastructure & Power Systems','entsoe-transparency')]['access_class']=='AUTH_REQUIRED'
    assert m[('Digital Connectivity','openstreetmap-telecom')]['access_class']=='LIVE'
    assert m[('Digital Connectivity','mlab-network-performance')]['access_class']=='DISCOVERY'
    assert m[('Digital Connectivity','fcc-broadband-data')]['access_class']=='DISCOVERY'

def test_osm_power_is_bounded(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,**kwargs:{'elements':[{'type':'node','id':1,'tags':{'power':'substation'}}]})
    with pytest.raises(ValueError): c.osm_power(settings(),latitude=0,longitude=0,radius_km=51)
    x=c.osm_power(settings(),latitude=41.88,longitude=-87.63,radius_km=5); assert x['record_count']==1 and x['connector_id']=='osm-power-overpass'

def test_osm_telecom_is_supplemental(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,**kwargs:{'elements':[{'id':2,'tags':{'communication:mobile_phone':'yes'}}]})
    x=c.osm_telecom(settings(),latitude=41.88,longitude=-87.63,radius_km=5); assert x['record_count']==1 and 'does not prove coverage' in x['boundary']

def test_eia_missing_key_is_configuration_required(monkeypatch):
    x=c.eia_electricity(settings(),route='electricity/rto/region-data'); assert not x['ok'] and x['configuration_key']=='SC_SI_EIA_API_KEY'
    monkeypatch.setattr(c,'_request_json',lambda url,**kwargs:{'response':{'data':[{'period':'2026-08-11T15','value':'100'}]}})
    y=c.eia_electricity(settings(eia_api_key='secret'),route='electricity/rto/region-data',data_field='value',facet_name='respondent',facet_value='MISO',length=10); assert y['ok'] and 'secret' not in y['provenance']['endpoint']

def test_ember_missing_key_and_live_payload(monkeypatch):
    assert c.ember_electricity(settings(),entity_code='USA')['configuration_required']
    monkeypatch.setattr(c,'_request_json',lambda url,**kwargs:[{'entity_code':'USA','date':'2026-01','generation_twh':1.2}])
    y=c.ember_electricity(settings(ember_api_key='ember-secret'),entity_code='USA'); assert y['record_count']==1 and 'ember-secret' not in y['provenance']['endpoint']

def test_entsoe_missing_token_and_xml(monkeypatch):
    x=c.entsoe_data(settings(),document_type='A65',period_start='202608010000',period_end='202608020000',domain_param='outBiddingZone_Domain',domain_code='10Y1001A1001A83F'); assert x['configuration_required']
    monkeypatch.setattr(c,'_request_text',lambda url,**kwargs:'<GL_MarketDocument><mRID>x</mRID></GL_MarketDocument>')
    y=c.entsoe_data(settings(entsoe_security_token='tok'),document_type='A65',period_start='202608010000',period_end='202608020000',domain_param='outBiddingZone_Domain',domain_code='10Y1001A1001A83F'); assert y['ok'] and 'tok' not in y['provenance']['endpoint']

def test_mlab_is_discovery_not_performance(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,**kwargs:{'results':[{'machine':'mlab1','location':{'country':'US'},'urls':{}}]})
    x=c.mlab_locate(settings()); assert x['mode']=='DISCOVERY' and 'not historical performance evidence' in x['boundary']

def test_fcc_is_discovery_not_installability(monkeypatch):
    monkeypatch.setattr(c,'_request_json',lambda url,**kwargs:{'data':['2026-06-30']})
    x=c.fcc_bdc_asofs(settings()); assert x['mode']=='DISCOVERY' and 'not measured performance' in x['boundary']

def test_public_routes_and_config_states():
    client=TestClient(app)
    assert client.get('/public/energy-systems/live/eia').status_code==200
    assert client.get('/public/energy-systems/live/ember',params={'entity_code':'USA'}).status_code==200
    assert client.get('/public/energy-systems/live/entsoe',params={'document_type':'A65','period_start':'202608010000','period_end':'202608020000','domain_param':'outBiddingZone_Domain','domain_code':'10Y1001A1001A83F'}).status_code==200
    assert client.get('/public/energy-systems/live/osm-power',params={'latitude':0,'longitude':0,'radius_km':51}).status_code==422

def test_audit_readiness_network_free():
    r=audit_readiness(settings()); assert r['ok'] and r['network_calls_performed'] is False

def test_external_health_never_blocks_release(): assert production_audit(settings())['checks']['external_source_health_not_used_as_release_blocker'] is True
