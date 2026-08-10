from fastapi.testclient import TestClient
from app.main import app
from app.geosphere_v42000 import catalog, normalize_measurement, normalize_notice, threshold_preview
client=TestClient(app)
def test_overview_and_catalog():
    o=client.get('/public/geosphere').json(); c=client.get('/public/geosphere/catalog').json()
    assert o['ok'] and o['version']=='4.32.0' and o['contract']=='global-geosphere-earthquake-volcano-intelligence'
    assert o['source_count']==4 and c['truth_boundaries']['shakemap_equals_structural_damage'] is False
    assert {'usgs-earthquake-catalog','usgs-shakemap','usgs-volcano-hans','nasa-jpl-aria'} <= {x['id'] for x in c['sources']}
def test_empty_state_has_no_hazard_claim():
    d=client.get('/public/geosphere/state',params={'source':'usgs-earthquake-catalog','indicator_type':'earthquake-event'}).json()
    assert d['ok'] and d['evidence']['event_loaded'] is False
    assert d['truth']['catalog_event_treated_as_emergency_warning'] is False
    assert d['truth']['zero_records_treated_as_no_hazard'] is False
def test_catalog_measurement_preserves_review_state():
    d=normalize_measurement({'source_id':'usgs-earthquake-catalog','source_url':'https://earthquake.usgs.gov/earthquakes/eventpage/us7000test','indicator_type':'magnitude','evidence_class':'seismic-event-catalog','value':6.4,'unit':'Mw','review_status':'automatic'})['measurement']
    assert d['review_status']=='automatic' and d['platform_warning_issued'] is False
def test_shakemap_not_damage():
    d=normalize_measurement({'source_id':'usgs-shakemap','source_url':'https://earthquake.usgs.gov/data/shakemap/','indicator_type':'shaking-intensity','evidence_class':'modeled-shaking-product','value':7,'unit':'MMI'})['measurement']
    assert d['shakemap_treated_as_structural_damage'] is False
def test_volcano_notice_remains_source_issued():
    d=normalize_notice({'source_id':'usgs-volcano-hans','source_url':'https://volcanoes.usgs.gov/vsc/api/hansApi/newest','indicator_type':'volcano-alert-level','evidence_class':'source-issued-volcano-notice','notice_id':'demo','alert_level':'WATCH','aviation_color_code':'ORANGE'})['notice']
    assert d['source_issued'] is True and d['platform_reissued'] is False and d['platform_escalated'] is False
def test_insar_not_vertical_or_damage():
    d=normalize_measurement({'source_id':'nasa-jpl-aria','source_url':'https://aria.jpl.nasa.gov/products/standard-displacement-products.html','indicator_type':'ground-displacement','evidence_class':'insar-displacement-product','value':0.12,'unit':'m','product_status':'preliminary'})['measurement']
    assert d['insar_treated_as_vertical_displacement'] is False and d['insar_treated_as_damage'] is False
def test_threshold_preview_no_platform_warning():
    p=threshold_preview({'value':7.0,'threshold':6.0,'operator':'>=','unit':'Mw'})['preview']
    assert p['comparison'] is True and p['earthquake_warning'] is False and p['volcano_alert'] is False and p['damage_finding'] is False
def test_readiness_and_export():
    r=client.get('/public/geosphere/readiness').json(); e=client.get('/public/geosphere/export-manifest').json()
    assert r['ok'] and all(r['checks'].values()) and e['review']['platform_volcano_alert'] is False
