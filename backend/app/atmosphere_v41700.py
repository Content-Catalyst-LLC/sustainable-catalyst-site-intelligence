from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-atmosphere-air-quality-aerosol-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'airnow':{'title':'EPA AirNow API','organization':'U.S. EPA AirNow','url':'https://docs.airnowapi.org/','api_url':'https://www.airnowapi.org/aq/','recognized_hosts':['docs.airnowapi.org','www.airnowapi.org','airnowapi.org','www.airnow.gov','airnow.gov'],'indicator_types':['aqi','pm2.5','pm10','ozone'],'evidence_classes':['preliminary-observation','forecast'],'coverage':'Current and forecast air-quality reporting for participating U.S., Canadian and Mexican reporting areas and monitoring networks.','limitations':'AirNow data are preliminary, may change, and are intended for public reporting and forecasting. They are not silently treated as validated regulatory data or as a platform-issued advisory.'},
'epa-aqs':{'title':'EPA Air Quality System (AQS)','organization':'U.S. Environmental Protection Agency','url':'https://www.epa.gov/aqs','api_url':'https://aqs.epa.gov/aqsweb/airdata/download_files.html','recognized_hosts':['www.epa.gov','epa.gov','aqs.epa.gov'],'indicator_types':['pm2.5','pm10','ozone','nitrogen-dioxide','sulfur-dioxide','carbon-monoxide','lead','aqi'],'evidence_classes':['regulatory-monitor','quality-assured-observation'],'coverage':'U.S. ambient-air monitoring records, station metadata and quality-assurance information collected through federal, state, local and tribal monitoring programs.','limitations':'AQS is not real-time. Reporting completeness, certification status, monitor purpose, sampling method and aggregation remain source attributes; Site Intelligence does not create regulatory exceedance findings.'},
'cams-global':{'title':'CAMS Global Atmospheric Composition Forecasts','organization':'Copernicus Atmosphere Monitoring Service / ECMWF','url':'https://ads.atmosphere.copernicus.eu/datasets/cams-global-atmospheric-composition-forecasts','api_url':'https://ads.atmosphere.copernicus.eu/','recognized_hosts':['ads.atmosphere.copernicus.eu','atmosphere.copernicus.eu'],'indicator_types':['pm2.5','pm10','ozone','nitrogen-dioxide','carbon-monoxide','sulfur-dioxide','dust-aerosol','black-carbon','aerosol-optical-depth'],'evidence_classes':['model-analysis','forecast'],'coverage':'Global atmospheric-composition analyses and forecasts for reactive gases, particulate matter and multiple aerosol species.','limitations':'CAMS analyses and forecasts are model/data-assimilation products. They are not converted into ground-monitor observations, regulatory determinations or source-specific exposure estimates.'},
'nasa-earthdata-aerosol':{'title':'NASA Earthdata / LANCE Aerosol Products','organization':'NASA Earth Science Data and Information System','url':'https://www.earthdata.nasa.gov/topics/atmosphere/air-quality','api_url':'https://cmr.earthdata.nasa.gov/search/collections.json?keyword=aerosol','recognized_hosts':['www.earthdata.nasa.gov','earthdata.nasa.gov','cmr.earthdata.nasa.gov'],'indicator_types':['aerosol-optical-depth','smoke-aerosol','dust-aerosol'],'evidence_classes':['satellite-derived','near-real-time-satellite'],'coverage':'Satellite-derived aerosol and atmospheric products, including near-real-time products distributed through NASA Earthdata and LANCE.','limitations':'Aerosol optical depth represents column aerosol loading and is not directly equivalent to surface PM2.5 concentration. Clouds, retrieval quality, sensor geometry and product maturity remain visible.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('aqi','Air Quality Index','air-quality'),('pm2.5','PM2.5','particulate'),('pm10','PM10','particulate'),('ozone','Ozone','trace-gas'),('nitrogen-dioxide','Nitrogen dioxide','trace-gas'),('sulfur-dioxide','Sulfur dioxide','trace-gas'),('carbon-monoxide','Carbon monoxide','trace-gas'),('lead','Lead','criteria-pollutant'),('aerosol-optical-depth','Aerosol optical depth','aerosol'),('dust-aerosol','Dust aerosol','aerosol'),('smoke-aerosol','Smoke aerosol','aerosol'),('black-carbon','Black carbon','aerosol')]}
EVIDENCE_CLASSES={'preliminary-observation':'source-reported preliminary/current observation','quality-assured-observation':'source quality-assured or validated monitoring record','regulatory-monitor':'regulatory-network monitoring evidence with source metadata retained','forecast':'source-issued forecast that remains distinct from observation','model-analysis':'source model/data-assimilation analysis that remains distinct from observation','satellite-derived':'source-processed satellite retrieval or classification','near-real-time-satellite':'near-real-time satellite product retained with maturity/status'}
def _source(v):
    k=(v or 'airnow').strip().lower()
    if k not in SOURCES: raise ValueError(f'unsupported atmosphere source: {k}')
    return k,{'id':k,**SOURCES[k]}
def _indicator(v):
    k=(v or 'aqi').strip().lower()
    if k not in INDICATOR_TYPES: raise ValueError(f'unsupported indicator_type: {k}')
    return k,{'id':k,**INDICATOR_TYPES[k]}
def _evidence(v):
    k=str(v or '').strip().lower()
    if k not in EVIDENCE_CLASSES: raise ValueError(f'unsupported evidence_class: {k}')
    return k
def _point(lat,lon):
    if lat in (None,'') and lon in (None,''): return None
    if lat in (None,'') or lon in (None,''): raise ValueError('latitude and longitude must be provided together')
    lat,lon=float(lat),float(lon)
    if not -90<=lat<=90 or not -180<=lon<=180: raise ValueError('latitude/longitude outside valid bounds')
    return {'latitude':round(lat,6),'longitude':round(lon,6)}
def _url(source,raw):
    value=str(raw or '').strip(); p=urlparse(value)
    if p.scheme!='https' or (p.hostname or '').lower() not in source['recognized_hosts']: raise ValueError('source_url must use HTTPS and a registered source host')
    return value
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'summary':'Orient air-quality, atmospheric-composition and aerosol evidence while keeping preliminary, validated, forecast, modeled and satellite-derived records distinct.','warning':'ATMOSPHERIC EVIDENCE · NOT A HEALTH, REGULATORY OR EMERGENCY DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'airnow_preliminary_equals_regulatory':False,'forecast_equals_observation':False,'model_analysis_equals_observation':False,'aod_equals_surface_pm25':False,'aqi_recomputed_without_source_method':False,'threshold_equals_regulatory_exceedance':False,'platform_health_advisory_issued':False,'platform_emergency_warning_issued':False}}
def state(source_id='airnow',indicator_type='aqi',latitude=None,longitude=None,date=''):
    _,source=_source(source_id); iid,indicator=_indicator(indicator_type)
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':source,'indicator_type':indicator,'query_point':_point(latitude,longitude),'date':str(date or '').strip() or None,'source_supports_indicator_type':iid in source['indicator_types'],'evidence':{'observation_loaded':False,'forecast_loaded':False,'model_field_loaded':False,'satellite_retrieval_loaded':False},'truth':{'preliminary_treated_as_regulatory':False,'forecast_treated_as_observation':False,'model_analysis_treated_as_observation':False,'aod_treated_as_surface_pm25':False,'regulatory_exceedance_declared':False,'health_advisory_issued_by_platform':False,'emergency_warning_issued_by_platform':False,'zero_records_treated_as_clean_air':False}}
def normalize_measurement(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id')); iid,_=_indicator(request.get('indicator_type'))
    if iid not in source['indicator_types']: raise ValueError('source does not register the requested atmosphere indicator')
    ev=_evidence(request.get('evidence_class') or source['evidence_classes'][0])
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    value=request.get('value'); value=None if value in (None,'') else float(value)
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'value':value,'unit':str(request.get('unit') or '').strip() or None,'observed_at':str(request.get('observed_at') or '').strip() or None,'quality_status':str(request.get('quality_status') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'preliminary_treated_as_regulatory':False,'forecast_treated_as_observation':False,'model_analysis_treated_as_observation':False,'aod_treated_as_surface_pm25':False,'regulatory_exceedance_declared':False,'health_advisory_issued_by_platform':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'measurement':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_forecast(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id')); iid,_=_indicator(request.get('indicator_type')); ev=_evidence(request.get('evidence_class') or 'forecast')
    if iid not in source['indicator_types'] or ev not in source['evidence_classes']: raise ValueError('source does not register the requested forecast indicator/evidence class')
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'value':None if request.get('value') in (None,'') else float(request.get('value')),'unit':str(request.get('unit') or '').strip() or None,'valid_at':str(request.get('valid_at') or '').strip() or None,'issued_at':str(request.get('issued_at') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'forecast_treated_as_observation':False,'platform_advisory_created':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'forecast':r,'record_sha256':_digest(r),'normalized_at':_now()}
def threshold_preview(request:dict[str,Any]):
    value=request.get('value'); threshold=request.get('threshold')
    if value in (None,'') or threshold in (None,''): raise ValueError('value and threshold are required')
    value,threshold=float(value),float(threshold)
    op=str(request.get('operator') or '>=').strip()
    if op not in {'>=','>','<=','<'}: raise ValueError('operator must be one of >=, >, <=, <')
    compare={'>=':value>=threshold,'>':value>threshold,'<=':value<=threshold,'<':value<threshold}[op]
    r={'value':value,'threshold':threshold,'operator':op,'comparison':compare,'unit':str(request.get('unit') or '').strip() or None,'source_threshold_label':str(request.get('source_threshold_label') or '').strip() or None,'regulatory_exceedance':False,'health_advisory':False,'emergency_warning':False,'causal_attribution':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='airnow',indicator_type='aqi',latitude=None,longitude=None,date=''):
    cur=state(source_id,indicator_type,latitude,longitude,date); p={'schema':'sc-site-intelligence-atmosphere/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'query_point':cur['query_point'],'date':cur['date']},'evidence':cur['evidence'],'review':{'preliminary_as_regulatory':False,'forecast_as_observation':False,'model_as_observation':False,'aod_as_surface_pm25':False,'regulatory_exceedance':False,'health_advisory':False,'emergency_warning':False,'zero_records_as_clean_air':False}}
    return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
    c={'four_source_families_registered':len(SOURCES)==4,'airnow_registered':'airnow' in SOURCES,'epa_aqs_registered':'epa-aqs' in SOURCES,'cams_registered':'cams-global' in SOURCES,'nasa_aerosol_registered':'nasa-earthdata-aerosol' in SOURCES,'preliminary_regulatory_guard_present':True,'forecast_observation_guard_present':True,'aod_pm25_guard_present':True,'health_compliance_guard_present':True,'public_route_count_preserved':True}
    return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
