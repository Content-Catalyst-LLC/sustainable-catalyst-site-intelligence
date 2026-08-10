from fastapi.testclient import TestClient
from app.main import app
from app.climate_intelligence_v42200 import normalize_measurement, normalize_extreme, threshold_preview
client=TestClient(app)
def test_overview_and_catalog():
    o=client.get('/public/climate').json(); c=client.get('/public/climate/catalog').json()
    assert o['ok'] and o['version']=='4.33.0' and o['contract']=='global-climate-baselines-anomalies-extremes-intelligence'
    assert o['source_count']==4 and c['truth_boundaries']['climate_normal_equals_forecast'] is False
    assert {'noaa-ncei-cdo','copernicus-era5','nasa-gistemp-v4','wmo-climate-extremes'} <= {x['id'] for x in c['sources']}
def test_empty_state_has_no_climate_risk_claim():
    d=client.get('/public/climate/state',params={'source':'noaa-ncei-cdo','indicator_type':'air-temperature'}).json()
    assert d['ok'] and d['evidence']['station_observation_loaded'] is False
    assert d['truth']['climate_normal_treated_as_forecast'] is False
    assert d['truth']['zero_records_treated_as_no_climate_risk'] is False
def test_noaa_normal_is_not_forecast():
    d=normalize_measurement({'source_id':'noaa-ncei-cdo','source_url':'https://www.ncei.noaa.gov/cdo-web/api/v2/data','indicator_type':'temperature-normal','evidence_class':'climate-normal','value':21.4,'unit':'C','normal_period':'1991-2020'})['measurement']
    assert d['climate_normal_treated_as_forecast'] is False and d['record_certification_issued'] is False
def test_era5_reanalysis_not_direct_observation():
    d=normalize_measurement({'source_id':'copernicus-era5','source_url':'https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries','indicator_type':'air-temperature','evidence_class':'climate-reanalysis','value':288.1,'unit':'K'})['measurement']
    assert d['reanalysis_treated_as_direct_observation'] is False
def test_era5t_preliminary_not_final():
    d=normalize_measurement({'source_id':'copernicus-era5','source_url':'https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries','indicator_type':'climate-anomaly','evidence_class':'preliminary-reanalysis','value':1.2,'unit':'C','processing_status':'ERA5T'})['measurement']
    assert d['preliminary_treated_as_final'] is False
def test_gistemp_anomaly_not_absolute_temperature_or_attribution():
    d=normalize_measurement({'source_id':'nasa-gistemp-v4','source_url':'https://data.giss.nasa.gov/gistemp/data_v4.html','indicator_type':'global-temperature-anomaly','evidence_class':'global-temperature-anomaly-series','value':1.1,'unit':'C','baseline_period':'1951-1980'})['measurement']
    assert d['anomaly_treated_as_absolute_local_temperature'] is False and d['attribution_claim_issued'] is False
def test_wmo_extreme_index_not_platform_certification():
    d=normalize_extreme({'source_id':'wmo-climate-extremes','source_url':'https://wmo.int/site/world-weather-and-climate-extremes-archive','indicator_type':'extreme-heat','evidence_class':'source-calculated-extreme-index','value':4.0,'unit':'days','methodology':'source-defined index'})['extreme']
    assert d['source_certified'] is False and d['platform_certified'] is False and d['attribution_claim'] is False
def test_threshold_readiness_and_export():
    p=threshold_preview({'value':2.0,'threshold':1.5,'operator':'>=','unit':'C'})['preview']; r=client.get('/public/climate/readiness').json(); e=client.get('/public/climate/export-manifest').json()
    assert p['comparison'] is True and p['weather_forecast'] is False and p['record_certification'] is False and p['attribution_finding'] is False
    assert r['ok'] and all(r['checks'].values()) and e['review']['anomaly_as_attribution'] is False
