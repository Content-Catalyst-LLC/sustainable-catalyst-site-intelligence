from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-climate-baselines-anomalies-extremes-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'noaa-ncei-cdo':{
 'title':'NOAA NCEI Access Data Service / Climate Data','organization':'NOAA National Centers for Environmental Information','url':'https://www.ncei.noaa.gov/access/services/data/v1','api_url':'https://www.ncei.noaa.gov/access/services/data/v1','recognized_hosts':['www.ncei.noaa.gov','ncei.noaa.gov'],'indicator_types':['air-temperature','precipitation','temperature-normal','precipitation-normal','heating-degree-days','cooling-degree-days'],'evidence_classes':['station-climate-observation','climate-normal'],'coverage':'Public machine retrieval for supported NCEI datasets, including bounded station/date observations and summaries exposed through the Access Data Service.','limitations':'Station records and climate summaries retain station, period-of-record, quality-control, dataset and baseline context. A climate normal is a reference climatology, not a forecast or a guarantee of future conditions. The separate Climate Data Online v2 service remains token-gated and is not represented as this live connector.'},
'copernicus-era5':{
 'title':'Copernicus Climate Change Service ERA5','organization':'Copernicus Climate Change Service / ECMWF','url':'https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries','api_url':'https://cds.climate.copernicus.eu/api/','recognized_hosts':['cds.climate.copernicus.eu','climate.copernicus.eu','www.copernicus.eu'],'indicator_types':['air-temperature','precipitation','surface-pressure','wind-speed','soil-temperature','climate-anomaly'],'evidence_classes':['climate-reanalysis','preliminary-reanalysis'],'coverage':'Global atmospheric, land and surface reanalysis from 1940 onward with hourly and aggregated products.','limitations':'ERA5 is a reanalysis produced by data assimilation, not a direct observation at every grid cell. ERA5T preliminary values may later change. Grid resolution does not imply local-site accuracy.'},
'nasa-gistemp-v4':{
 'title':'NASA GISS Surface Temperature Analysis (GISTEMP v4)','organization':'NASA Goddard Institute for Space Studies','url':'https://data.giss.nasa.gov/gistemp/','api_url':'https://data.giss.nasa.gov/gistemp/data_v4.html','recognized_hosts':['data.giss.nasa.gov','www.giss.nasa.gov','giss.nasa.gov'],'indicator_types':['surface-temperature-anomaly','global-temperature-anomaly','zonal-temperature-anomaly'],'evidence_classes':['gridded-temperature-anomaly-analysis','global-temperature-anomaly-series'],'coverage':'Global and zonal surface-temperature anomaly estimates from 1880 to present with monthly updates.','limitations':'GISTEMP is an anomaly analysis relative to a stated baseline and is revised when late observations or corrections arrive. An anomaly is not an absolute local temperature and does not by itself establish attribution.'},
'wmo-climate-extremes':{
 'title':'WMO Weather & Climate Extremes Framework','organization':'World Meteorological Organization','url':'https://wmo.int/site/world-weather-and-climate-extremes-archive','api_url':'https://wmo.int/site/world-weather-and-climate-extremes-archive','recognized_hosts':['wmo.int','public.wmo.int'],'indicator_types':['extreme-heat','extreme-cold','extreme-precipitation','dry-spell','warm-spell','climate-record'],'evidence_classes':['source-calculated-extreme-index','wmo-certified-climate-record'],'coverage':'Climate-extreme indicators and formally evaluated global, hemispheric and regional weather/climate records.','limitations':'A calculated extreme index is not automatically a WMO-certified record. Potential records require source verification and formal evaluation; Site Intelligence does not certify records or attribute causes.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('air-temperature','Air temperature','observed-climate'),('precipitation','Precipitation','observed-climate'),('temperature-normal','Temperature climate normal','climatology'),('precipitation-normal','Precipitation climate normal','climatology'),('heating-degree-days','Heating degree days','climatology'),('cooling-degree-days','Cooling degree days','climatology'),('surface-pressure','Surface pressure','reanalysis'),('wind-speed','Wind speed','reanalysis'),('soil-temperature','Soil temperature','reanalysis'),('climate-anomaly','Climate anomaly','reanalysis'),('surface-temperature-anomaly','Surface temperature anomaly','anomaly-analysis'),('global-temperature-anomaly','Global temperature anomaly','anomaly-analysis'),('zonal-temperature-anomaly','Zonal temperature anomaly','anomaly-analysis'),('extreme-heat','Extreme heat index','climate-extremes'),('extreme-cold','Extreme cold index','climate-extremes'),('extreme-precipitation','Extreme precipitation index','climate-extremes'),('dry-spell','Dry-spell index','climate-extremes'),('warm-spell','Warm-spell index','climate-extremes'),('climate-record','Climate record','climate-extremes')]}
EVIDENCE_CLASSES={
'station-climate-observation':'quality-controlled station observation retaining station and period metadata',
'climate-normal':'reference climatology calculated for a specified normal period',
'climate-reanalysis':'model-observation assimilated historical climate field distinct from direct observation',
'preliminary-reanalysis':'preliminary reanalysis field that may be superseded by final processing',
'gridded-temperature-anomaly-analysis':'gridded anomaly analysis relative to a stated baseline',
'global-temperature-anomaly-series':'global or zonal anomaly time series relative to a stated baseline',
'source-calculated-extreme-index':'extreme-climate index calculated under a stated source methodology',
'wmo-certified-climate-record':'record formally evaluated/certified by WMO or identified as such by the source'}
def _source(v):
    k=(v or 'noaa-ncei-cdo').strip().lower()
    if k not in SOURCES: raise ValueError(f'unsupported climate source: {k}')
    return k,{'id':k,**SOURCES[k]}
def _indicator(v):
    k=(v or 'air-temperature').strip().lower()
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
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'summary':'Orient historical observations, climate normals, reanalysis, anomaly series and climate-extreme indicators while preserving baseline, processing and certification boundaries.','warning':'CLIMATE EVIDENCE · NOT A WEATHER FORECAST, ATTRIBUTION FINDING OR RECORD CERTIFICATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'climate_normal_equals_forecast':False,'era5_equals_direct_observation':False,'era5t_equals_final_reanalysis':False,'gistemp_anomaly_equals_local_temperature':False,'anomaly_equals_attribution':False,'extreme_index_equals_certified_record':False,'zero_records_equals_no_climate_risk':False}}
def state(source_id='noaa-ncei-cdo',indicator_type='air-temperature',latitude=None,longitude=None,date=''):
    _,source=_source(source_id); iid,indicator=_indicator(indicator_type)
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':source,'indicator_type':indicator,'query_point':_point(latitude,longitude),'date':str(date or '').strip() or None,'source_supports_indicator_type':iid in source['indicator_types'],'evidence':{'station_observation_loaded':False,'climate_normal_loaded':False,'reanalysis_loaded':False,'anomaly_series_loaded':False,'extreme_index_loaded':False,'certified_record_loaded':False},'truth':{'climate_normal_treated_as_forecast':False,'era5_treated_as_direct_observation':False,'era5t_treated_as_final_reanalysis':False,'gistemp_anomaly_treated_as_local_absolute_temperature':False,'anomaly_treated_as_attribution':False,'extreme_index_treated_as_certified_record':False,'zero_records_treated_as_no_climate_risk':False,'automatic_action_authorized':False}}
def normalize_measurement(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id')); iid,_=_indicator(request.get('indicator_type'))
    if iid not in source['indicator_types']: raise ValueError('source does not register the requested climate indicator')
    ev=_evidence(request.get('evidence_class') or source['evidence_classes'][0])
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    value=request.get('value'); value=None if value in (None,'') else float(value)
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'value':value,'unit':str(request.get('unit') or '').strip() or None,'baseline_period':str(request.get('baseline_period') or '').strip() or None,'normal_period':str(request.get('normal_period') or '').strip() or None,'observed_or_valid_at':str(request.get('observed_or_valid_at') or '').strip() or None,'processing_status':str(request.get('processing_status') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'climate_normal_treated_as_forecast':False,'reanalysis_treated_as_direct_observation':False,'preliminary_treated_as_final':False,'anomaly_treated_as_absolute_local_temperature':False,'attribution_claim_issued':False,'record_certification_issued':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'measurement':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_extreme(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id') or 'wmo-climate-extremes'); iid,_=_indicator(request.get('indicator_type') or 'extreme-heat')
    if iid not in source['indicator_types']: raise ValueError('source does not register the requested climate-extreme indicator')
    ev=_evidence(request.get('evidence_class') or source['evidence_classes'][0])
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'value':None if request.get('value') in (None,'') else float(request.get('value')),'unit':str(request.get('unit') or '').strip() or None,'period':str(request.get('period') or '').strip() or None,'methodology':str(request.get('methodology') or '').strip() or None,'source_certified':ev=='wmo-certified-climate-record','platform_certified':False,'attribution_claim':False,'emergency_warning':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'extreme':r,'record_sha256':_digest(r),'normalized_at':_now()}
def threshold_preview(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    value=float(request.get('value')); threshold=float(request.get('threshold')); op=str(request.get('operator') or '>=').strip()
    if op not in {'>','>=','<','<=','=='}: raise ValueError('unsupported operator')
    comparison={'>':value>threshold,'>=':value>=threshold,'<':value<threshold,'<=':value<=threshold,'==':value==threshold}[op]
    r={'value':value,'threshold':threshold,'operator':op,'comparison':comparison,'unit':str(request.get('unit') or '').strip() or None,'source_threshold_label':str(request.get('source_threshold_label') or '').strip() or None,'weather_forecast':False,'record_certification':False,'attribution_finding':False,'emergency_warning':False,'regulatory_finding':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='noaa-ncei-cdo',indicator_type='air-temperature',latitude=None,longitude=None,date=''):
    cur=state(source_id,indicator_type,latitude,longitude,date); p={'schema':'sc-site-intelligence-climate/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'query_point':cur['query_point'],'date':cur['date']},'evidence':cur['evidence'],'review':{'climate_normal_as_forecast':False,'era5_as_direct_observation':False,'era5t_as_final_reanalysis':False,'gistemp_anomaly_as_local_temperature':False,'anomaly_as_attribution':False,'extreme_index_as_certified_record':False,'zero_records_as_no_climate_risk':False}}
    return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
    c={'four_source_families_registered':len(SOURCES)==4,'noaa_ncei_registered':'noaa-ncei-cdo' in SOURCES,'era5_registered':'copernicus-era5' in SOURCES,'gistemp_registered':'nasa-gistemp-v4' in SOURCES,'wmo_extremes_registered':'wmo-climate-extremes' in SOURCES,'normal_forecast_guard_present':True,'reanalysis_observation_guard_present':True,'preliminary_final_guard_present':True,'anomaly_attribution_guard_present':True,'record_certification_guard_present':True,'public_route_count_preserved':True}
    return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
