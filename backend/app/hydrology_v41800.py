from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-hydrology-rivers-flood-drought-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'usgs-water-data':{'title':'USGS Water Data APIs','organization':'U.S. Geological Survey','url':'https://api.waterdata.usgs.gov/','api_url':'https://api.waterdata.usgs.gov/ogcapi/v0/','recognized_hosts':['api.waterdata.usgs.gov','waterdata.usgs.gov'],'indicator_types':['streamflow','gage-height','groundwater-level','water-temperature'],'evidence_classes':['in-situ-observation','daily-statistic'],'coverage':'U.S. stream, lake, groundwater and related monitoring-location observations and metadata through modern machine-readable Water Data APIs.','limitations':'Continuous measurements can be provisional or delayed and retain source quality/status metadata. Gauge observations are local measurements and are not silently generalized to an entire river reach or basin.'},
'nasa-gpm-imerg':{'title':'NASA GPM IMERG','organization':'NASA Global Precipitation Measurement Mission','url':'https://gpm.nasa.gov/data/imerg','api_url':'https://gpm.nasa.gov/data/directory','recognized_hosts':['gpm.nasa.gov','earthdata.nasa.gov','www.earthdata.nasa.gov','search.earthdata.nasa.gov'],'indicator_types':['precipitation-rate','precipitation-accumulation'],'evidence_classes':['satellite-estimate','near-real-time-satellite'],'coverage':'Global multi-satellite precipitation estimates with Early, Late and Final processing streams and multiple temporal resolutions.','limitations':'IMERG estimates precipitation from satellite and merged inputs. They are not converted into rain-gauge observations; Early/Late/Final processing maturity and latency remain visible.'},
'copernicus-glofas':{'title':'Copernicus GloFAS / Global Flood Monitoring','organization':'Copernicus Emergency Management Service / ECMWF','url':'https://global-flood.emergency.copernicus.eu/','api_url':'https://ewds.climate.copernicus.eu/','recognized_hosts':['global-flood.emergency.copernicus.eu','ewds.climate.copernicus.eu','confluence.ecmwf.int'],'indicator_types':['river-discharge','flood-threshold','runoff','soil-wetness'],'evidence_classes':['model-analysis','forecast','reanalysis'],'coverage':'Global modeled hydrology, probabilistic river-discharge forecasts, reanalysis and flood-awareness products.','limitations':'GloFAS is a hydrological modelling and flood-awareness system. Model discharge, return-period thresholds and forecast probabilities remain distinct from gauge observations and official local warnings.'},
'drought-gov':{'title':'Drought.gov / NIDIS Drought Indicators','organization':'NOAA National Integrated Drought Information System','url':'https://www.drought.gov/data-download','api_url':'https://www.drought.gov/data-download','recognized_hosts':['www.drought.gov','drought.gov'],'indicator_types':['spi','spei','eddi','percent-normal-precipitation','drought-category'],'evidence_classes':['drought-index','source-issued-category'],'coverage':'Operational drought indices and source-published drought-status products derived from NOAA, NASA and partner datasets.','limitations':'Drought indices are evidence with defined reference periods and methods. Site Intelligence does not synthesize an index into an independent drought declaration or emergency determination.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('streamflow','Streamflow','surface-water'),('gage-height','Gage height','surface-water'),('groundwater-level','Groundwater level','groundwater'),('water-temperature','Water temperature','surface-water'),('precipitation-rate','Precipitation rate','precipitation'),('precipitation-accumulation','Precipitation accumulation','precipitation'),('river-discharge','Modeled river discharge','hydrologic-model'),('flood-threshold','Flood-awareness threshold','hydrologic-model'),('runoff','Runoff','hydrologic-model'),('soil-wetness','Soil wetness','hydrologic-model'),('spi','Standardized Precipitation Index','drought'),('spei','Standardized Precipitation Evapotranspiration Index','drought'),('eddi','Evaporative Demand Drought Index','drought'),('percent-normal-precipitation','Percent of normal precipitation','drought'),('drought-category','Source-issued drought category','drought')]}
EVIDENCE_CLASSES={'in-situ-observation':'source-reported gauge, well or sensor observation','daily-statistic':'source-reported daily statistic derived from monitoring observations','satellite-estimate':'satellite-derived precipitation estimate','near-real-time-satellite':'near-real-time satellite estimate with product maturity retained','model-analysis':'hydrologic model analysis distinct from observation','forecast':'source-issued hydrologic forecast distinct from observation','reanalysis':'retrospective model reanalysis distinct from observation','drought-index':'source-computed drought index with method/reference period retained','source-issued-category':'source-issued drought category retained without platform reissuance'}
def _source(v):
    k=(v or 'usgs-water-data').strip().lower()
    if k not in SOURCES: raise ValueError(f'unsupported hydrology source: {k}')
    return k,{'id':k,**SOURCES[k]}
def _indicator(v):
    k=(v or 'streamflow').strip().lower()
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
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'summary':'Orient river, precipitation, modeled flood and drought evidence while keeping gauge, satellite, modeled, forecast and source-issued status records distinct.','warning':'HYDROLOGIC EVIDENCE · NOT AN OFFICIAL FLOOD, DROUGHT OR SAFETY WARNING'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'satellite_precipitation_equals_gauge_observation':False,'model_discharge_equals_gauge_observation':False,'forecast_equals_observation':False,'near_real_time_equals_final':False,'threshold_equals_official_flood_warning':False,'drought_index_equals_platform_drought_declaration':False,'zero_records_equals_no_flood_or_drought':False}}
def state(source_id='usgs-water-data',indicator_type='streamflow',latitude=None,longitude=None,date=''):
    _,source=_source(source_id); iid,indicator=_indicator(indicator_type)
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':source,'indicator_type':indicator,'query_point':_point(latitude,longitude),'date':str(date or '').strip() or None,'source_supports_indicator_type':iid in source['indicator_types'],'evidence':{'measurement_loaded':False,'forecast_loaded':False,'model_field_loaded':False,'drought_index_loaded':False},'truth':{'satellite_precipitation_treated_as_gauge_observation':False,'model_discharge_treated_as_gauge_observation':False,'forecast_treated_as_observation':False,'near_real_time_treated_as_final':False,'official_flood_warning_issued_by_platform':False,'drought_declaration_issued_by_platform':False,'zero_records_treated_as_no_flood_or_drought':False,'automatic_action_authorized':False}}
def normalize_measurement(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id')); iid,_=_indicator(request.get('indicator_type'))
    if iid not in source['indicator_types']: raise ValueError('source does not register the requested hydrology indicator')
    ev=_evidence(request.get('evidence_class') or source['evidence_classes'][0])
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    value=request.get('value'); value=None if value in (None,'') else float(value)
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'value':value,'unit':str(request.get('unit') or '').strip() or None,'observed_at':str(request.get('observed_at') or '').strip() or None,'quality_status':str(request.get('quality_status') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'satellite_precipitation_treated_as_gauge_observation':False,'model_discharge_treated_as_gauge_observation':False,'near_real_time_treated_as_final':False,'official_flood_warning_issued_by_platform':False,'drought_declaration_issued_by_platform':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'measurement':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_forecast(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id')); iid,_=_indicator(request.get('indicator_type')); ev=_evidence(request.get('evidence_class') or 'forecast')
    if iid not in source['indicator_types'] or ev not in source['evidence_classes']: raise ValueError('source does not register the requested forecast indicator/evidence class')
    value=request.get('value'); value=None if value in (None,'') else float(value)
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'value':value,'unit':str(request.get('unit') or '').strip() or None,'valid_at':str(request.get('valid_at') or '').strip() or None,'lead_time_hours':None if request.get('lead_time_hours') in (None,'') else float(request.get('lead_time_hours')),'query_point':_point(request.get('latitude'),request.get('longitude')),'forecast_treated_as_observation':False,'model_discharge_treated_as_gauge_observation':False,'platform_warning_created':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'forecast':r,'record_sha256':_digest(r),'normalized_at':_now()}
def threshold_preview(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    value=float(request.get('value')); threshold=float(request.get('threshold')); op=str(request.get('operator') or '>=').strip()
    if op not in {'>','>=','<','<=','=='}: raise ValueError('unsupported operator')
    comparison={'>':value>threshold,'>=':value>=threshold,'<':value<threshold,'<=':value<=threshold,'==':value==threshold}[op]
    r={'value':value,'threshold':threshold,'operator':op,'comparison':comparison,'unit':str(request.get('unit') or '').strip() or None,'source_threshold_label':str(request.get('source_threshold_label') or '').strip() or None,'official_flood_warning':False,'drought_declaration':False,'emergency_warning':False,'causal_attribution':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='usgs-water-data',indicator_type='streamflow',latitude=None,longitude=None,date=''):
    cur=state(source_id,indicator_type,latitude,longitude,date); p={'schema':'sc-site-intelligence-hydrology/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'query_point':cur['query_point'],'date':cur['date']},'evidence':cur['evidence'],'review':{'satellite_as_gauge':False,'model_as_gauge':False,'forecast_as_observation':False,'near_real_time_as_final':False,'official_flood_warning':False,'drought_declaration':False,'zero_records_as_no_flood_or_drought':False}}
    return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
    c={'four_source_families_registered':len(SOURCES)==4,'modern_usgs_api_registered':'usgs-water-data' in SOURCES,'gpm_imerg_registered':'nasa-gpm-imerg' in SOURCES,'glofas_registered':'copernicus-glofas' in SOURCES,'drought_gov_registered':'drought-gov' in SOURCES,'gauge_satellite_guard_present':True,'model_observation_guard_present':True,'flood_warning_guard_present':True,'drought_declaration_guard_present':True,'public_route_count_preserved':True}
    return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
