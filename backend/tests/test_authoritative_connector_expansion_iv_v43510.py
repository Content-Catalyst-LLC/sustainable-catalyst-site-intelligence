from fastapi.testclient import TestClient
import pytest
from app.config import Settings
from app.main import app
from app import authoritative_connectors_v43510 as c
from app.authoritative_api_audit_v43510 import audit_overview, audit_readiness
from app.authoritative_api_production_audit_v43510 import production_audit, closure_ledger


def settings(): return Settings(_env_file=None)

def test_catalog_has_25_interfaces_and_five_expansion_iv():
    result=c.connector_catalog(settings())
    assert result['connector_count']==25
    assert result['live_connector_count']==21
    assert result['discovery_connector_count']==2
    assert result['auth_required_connector_count']==2
    assert result['expansion_iv_connector_count']==5
    assert {x['id'] for x in c.NEW_CONNECTORS}.issubset({x['id'] for x in result['connectors']})

def test_readiness_is_network_free():
    result=c.connector_readiness(settings())
    assert result['ok'] is True and result['network_calls_performed'] is False

def test_faostat_requires_bounded_dimension_and_preserves_payload(monkeypatch):
    monkeypatch.setattr(c.shared,'_request_json',lambda url,**kwargs:{'data':[{'Area':'Palestine','Year':2024,'Value':1.2,'Unit':'x','Flag':'A'}]})
    with pytest.raises(ValueError): c.faostat_data(settings(),domain='QCL')
    result=c.faostat_data(settings(),domain='QCL',area='299',year='2024',limit=10)
    assert result['connector_id']=='faostat-data-api' and result['data']['data'][0]['Year']==2024
    assert 'show_flags=true' in result['provenance']['endpoint'] and 'show_notes=true' in result['provenance']['endpoint']

def test_ilostat_bounded_area_and_time(monkeypatch):
    monkeypatch.setattr(c.shared,'_request_json',lambda url,**kwargs:{'data':[{'ref_area':'PSE','time':2024,'obs_value':12.3}]})
    result=c.ilostat_indicator(settings(),indicator='UNE_DEAP_SEX_AGE_RT_A',ref_area='PSE',start_year=2020,end_year=2024)
    assert result['ref_area']=='PSE' and result['data']['data'][0]['obs_value']==12.3
    with pytest.raises(ValueError): c.ilostat_indicator(settings(),indicator='x',ref_area='PSE',start_year=1950,end_year=2024)

def test_oecd_rejects_unbounded_all_and_preserves_rows(monkeypatch):
    monkeypatch.setattr(c.shared,'_request_csv',lambda url,**kwargs:[{'REF_AREA':'USA','TIME_PERIOD':'2024','OBS_VALUE':'1.0'}])
    with pytest.raises(ValueError): c.oecd_sdmx_data(settings(),agency='OECD.SDD.NAD',dataflow='DSD_NAAG@DF_NAAG_I',key='all')
    result=c.oecd_sdmx_data(settings(),agency='OECD.SDD.NAD',dataflow='DSD_NAAG@DF_NAAG_I',key='USA.A')
    assert result['row_count']==1 and result['data'][0]['REF_AREA']=='USA'

def test_epa_frs_requires_bounded_query_and_respects_25_mile_limit(monkeypatch):
    monkeypatch.setattr(c.shared,'_request_json',lambda url,**kwargs:{'Facilities':[{'RegistryId':'110000000001'}]})
    with pytest.raises(ValueError): c.epa_frs_facilities(settings())
    with pytest.raises(ValueError): c.epa_frs_facilities(settings(),latitude=38.8,longitude=-77.01,search_radius=26)
    result=c.epa_frs_facilities(settings(),state_abbr='VA',city_name='Newport News',facility_name='Mobil Oil')
    assert result['data']['Facilities'][0]['RegistryId']=='110000000001'

def test_usgs_hans_is_bounded_to_documented_recent_window(monkeypatch):
    monkeypatch.setattr(c.shared,'_request_json',lambda url,**kwargs:[{'noticeId':'n1','volcano':'Example'}])
    with pytest.raises(ValueError): c.usgs_volcano_notices(settings(),days=8)
    result=c.usgs_volcano_notices(settings(),days=3,observatory='hvo')
    assert result['days']==3 and result['observatory']=='hvo' and result['data'][0]['noticeId']=='n1'

def test_audit_closes_existing_hans_gap_and_adds_four_interfaces():
    o=audit_overview(settings())
    assert o['summary']['source_registrations']==188
    assert o['summary']['machine_readable_registrations']==105
    assert o['summary']['counts']['STALE']==0
    rows=[]
    from app.authoritative_api_audit_v43510 import source_inventory
    rows=source_inventory(settings())
    hans=[r for r in rows if r['source_id']=='usgs-volcano-hans']
    assert len(hans)==1 and hans[0]['access_class']=='LIVE'

def test_production_machine_backlog_drops_to_43():
    p=production_audit(settings())
    assert p['production_controls_ready'] is True
    assert p['machine_readable_summary']['registrations']==105
    assert p['machine_readable_summary']['registered_not_retrieved']==43
    assert p['machine_readable_summary']['counts']['LIVE']==41
    assert p['coverage']['registered_not_retrieved_pct_of_machine_readable']==40.95

def test_closure_ledger_remains_explicit():
    l=closure_ledger(settings())
    assert l['summary']['registered_not_retrieved']==43
    assert l['summary']['stale']==0
    assert l['summary']['machine_readable_gap_records']==58

def test_audit_readiness_green_without_network():
    r=audit_readiness(settings())
    assert r['ok'] is True and r['network_calls_performed'] is False

def test_public_catalog_and_readiness_routes_use_43510():
    client=TestClient(app)
    assert client.get('/public/authoritative-connectors').json()['connector_count']==35
    assert client.get('/public/authoritative-connectors/readiness').json()['version']=='4.35.12'

def test_new_routes_exist_and_validate_before_network():
    client=TestClient(app)
    assert client.get('/public/authoritative-connectors/faostat/data',params={'domain':'QCL'}).status_code==400
    assert client.get('/public/authoritative-connectors/oecd/sdmx',params={'agency':'OECD.SDD.NAD','dataflow':'DF','key':'all'}).status_code==400
    assert client.get('/public/authoritative-connectors/epa-frs/facilities').status_code==400
    assert client.get('/public/authoritative-connectors/usgs-volcano/notices',params={'days':8}).status_code==422

def test_no_external_source_health_becomes_release_blocker():
    p=production_audit(settings())
    assert p['checks']['external_source_health_not_used_as_release_blocker'] is True
