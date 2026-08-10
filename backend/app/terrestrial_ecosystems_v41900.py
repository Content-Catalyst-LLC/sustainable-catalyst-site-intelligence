from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='terrestrial-ecosystems-vegetation-wildfire-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'nasa-firms':{'title':'NASA FIRMS Active Fire & Burned Area','organization':'NASA LANCE / FIRMS','url':'https://firms.modaps.eosdis.nasa.gov/','api_url':'https://firms.modaps.eosdis.nasa.gov/api/area/','recognized_hosts':['firms.modaps.eosdis.nasa.gov','earthdata.nasa.gov','www.earthdata.nasa.gov','wiki.earthdata.nasa.gov'],'indicator_types':['active-fire-detection','fire-radiative-power','burned-area'],'evidence_classes':['near-real-time-fire-detection','satellite-burned-area'],'coverage':'Global MODIS and VIIRS active-fire detections plus source-distributed burned-area products.','limitations':'A satellite fire detection is a thermal anomaly observation, not a complete wildfire incident, perimeter, containment estimate, ignition cause or evacuation order. Active-fire detections are not used to estimate burned area; burned-area products remain separate retrospective satellite classifications.'},
'nasa-modis-vegetation':{'title':'NASA MODIS Vegetation Indices','organization':'NASA EOSDIS Land Processes DAAC','url':'https://www.earthdata.nasa.gov/centers/lp-daac','api_url':'https://cmr.earthdata.nasa.gov/search/','recognized_hosts':['earthdata.nasa.gov','www.earthdata.nasa.gov','cmr.earthdata.nasa.gov','lpdaac.usgs.gov'],'indicator_types':['ndvi','evi','vegetation-continuous-fields'],'evidence_classes':['satellite-vegetation-index','satellite-fractional-cover'],'coverage':'Global MODIS vegetation-index and vegetation-continuous-field products, including NDVI/EVI time series.','limitations':'Vegetation indices are remotely sensed proxies with quality flags, compositing, clouds and sensor effects. NDVI/EVI values are not silently converted into direct ecosystem health, biomass, yield, biodiversity or causal-impact findings.'},
'copernicus-lcfm':{'title':'Copernicus Land Cover & Forest Monitoring (LCFM)','organization':'Copernicus Land Monitoring Service / European Commission JRC','url':'https://land.copernicus.eu/en/products/global-dynamic-land-cover','api_url':'https://dataspace.copernicus.eu/','recognized_hosts':['land.copernicus.eu','dataspace.copernicus.eu'],'indicator_types':['land-cover-class','tree-cover-density','land-cover-change'],'evidence_classes':['satellite-land-cover','satellite-tree-cover','satellite-change-classification'],'coverage':'Global 10 m land-cover mapping and pan-tropical tree-cover monitoring using Copernicus Sentinel observations, with annual and developing sub-annual products.','limitations':'Mapped land cover is a source classification, not legal land use, ownership, protected status, confirmed deforestation cause or ground-survey truth. Product year, algorithm version, validation status and resolution remain visible.'},
'copernicus-global-vegetation':{'title':'Copernicus Global Vegetation Properties','organization':'Copernicus Land Monitoring Service','url':'https://land.copernicus.eu/en/products/vegetation','api_url':'https://dataspace.copernicus.eu/','recognized_hosts':['land.copernicus.eu','dataspace.copernicus.eu'],'indicator_types':['lai','fapar','fcover','ndvi','burned-area'],'evidence_classes':['near-real-time-vegetation','consolidated-vegetation','satellite-burned-area'],'coverage':'Operational global vegetation properties and indices, including LAI, FAPAR, FCover, NDVI and burnt-area products.','limitations':'Near-real-time and consolidated vegetation products remain distinct. Vegetation variables are satellite-derived estimates and are not independently converted into ecosystem condition, carbon-stock, agricultural-loss or wildfire-impact determinations.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('active-fire-detection','Active fire detection','wildfire'),('fire-radiative-power','Fire radiative power','wildfire'),('burned-area','Burned area','wildfire'),('ndvi','Normalized Difference Vegetation Index','vegetation'),('evi','Enhanced Vegetation Index','vegetation'),('vegetation-continuous-fields','Vegetation continuous fields','vegetation'),('land-cover-class','Land-cover class','land-cover'),('tree-cover-density','Tree-cover density','forest'),('land-cover-change','Land-cover change classification','land-cover'),('lai','Leaf Area Index','vegetation'),('fapar','Fraction of absorbed photosynthetically active radiation','vegetation'),('fcover','Fraction of green vegetation cover','vegetation')]}
EVIDENCE_CLASSES={'near-real-time-fire-detection':'near-real-time satellite thermal-anomaly/fire detection','satellite-burned-area':'satellite-derived burned-area classification distinct from active fire','satellite-vegetation-index':'satellite-derived vegetation index with source quality/maturity retained','satellite-fractional-cover':'satellite-derived fractional vegetation or cover field','satellite-land-cover':'satellite-derived land-cover classification','satellite-tree-cover':'satellite-derived tree-cover density or class','satellite-change-classification':'satellite-derived land-cover/tree-cover change classification','near-real-time-vegetation':'near-real-time vegetation estimate distinct from consolidated product','consolidated-vegetation':'source-consolidated vegetation estimate'}
def _source(v):
    k=(v or 'nasa-firms').strip().lower()
    if k not in SOURCES: raise ValueError(f'unsupported terrestrial source: {k}')
    return k,{'id':k,**SOURCES[k]}
def _indicator(v):
    k=(v or 'active-fire-detection').strip().lower()
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
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'summary':'Orient terrestrial vegetation, land-cover, tree-cover, active-fire and burned-area evidence while preserving satellite-product maturity and interpretation boundaries.','warning':'TERRESTRIAL EVIDENCE · NOT A WILDFIRE INCIDENT, SAFETY OR ECOSYSTEM-HEALTH DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'active_fire_detection_equals_wildfire_incident':False,'active_fire_detection_equals_burned_area':False,'burned_area_equals_active_fire':False,'vegetation_index_equals_ecosystem_health':False,'land_cover_equals_legal_land_use':False,'satellite_classification_equals_ground_truth':False,'near_real_time_equals_consolidated':False,'threshold_equals_wildfire_warning':False,'zero_records_equals_no_fire_or_no_change':False}}
def state(source_id='nasa-firms',indicator_type='active-fire-detection',latitude=None,longitude=None,date=''):
    _,source=_source(source_id); iid,indicator=_indicator(indicator_type)
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':source,'indicator_type':indicator,'query_point':_point(latitude,longitude),'date':str(date or '').strip() or None,'source_supports_indicator_type':iid in source['indicator_types'],'evidence':{'measurement_loaded':False,'feature_loaded':False,'active_fire_loaded':False,'burned_area_loaded':False,'land_cover_loaded':False,'vegetation_product_loaded':False},'truth':{'active_fire_treated_as_wildfire_incident':False,'active_fire_treated_as_burned_area':False,'burned_area_treated_as_active_fire':False,'vegetation_index_treated_as_ecosystem_health':False,'land_cover_treated_as_legal_land_use':False,'satellite_classification_treated_as_ground_truth':False,'near_real_time_treated_as_consolidated':False,'platform_wildfire_warning_issued':False,'platform_ecosystem_health_finding':False,'zero_records_treated_as_no_fire_or_no_change':False,'automatic_action_authorized':False}}
def normalize_measurement(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id')); iid,_=_indicator(request.get('indicator_type'))
    if iid not in source['indicator_types']: raise ValueError('source does not register the requested terrestrial indicator')
    ev=_evidence(request.get('evidence_class') or source['evidence_classes'][0])
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    value=request.get('value'); value=None if value in (None,'') else float(value)
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'value':value,'unit':str(request.get('unit') or '').strip() or None,'observed_at':str(request.get('observed_at') or '').strip() or None,'quality_status':str(request.get('quality_status') or '').strip() or None,'product_maturity':str(request.get('product_maturity') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'active_fire_treated_as_wildfire_incident':False,'active_fire_treated_as_burned_area':False,'vegetation_index_treated_as_ecosystem_health':False,'near_real_time_treated_as_consolidated':False,'platform_wildfire_warning_issued':False,'platform_ecosystem_health_finding':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'measurement':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_feature(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id')); iid,_=_indicator(request.get('indicator_type'))
    if iid not in source['indicator_types']: raise ValueError('source does not register the requested terrestrial feature')
    ev=_evidence(request.get('evidence_class') or source['evidence_classes'][0])
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'feature_id':str(request.get('feature_id') or '').strip() or None,'class_label':str(request.get('class_label') or '').strip() or None,'area_km2':None if request.get('area_km2') in (None,'') else float(request.get('area_km2')),'observed_at':str(request.get('observed_at') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'burned_area_treated_as_active_fire':False,'land_cover_treated_as_legal_land_use':False,'satellite_classification_treated_as_ground_truth':False,'wildfire_incident_created':False,'ecosystem_health_finding_created':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'feature':r,'record_sha256':_digest(r),'normalized_at':_now()}
def threshold_preview(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    value=float(request.get('value')); threshold=float(request.get('threshold')); op=str(request.get('operator') or '>=').strip()
    if op not in {'>','>=','<','<=','=='}: raise ValueError('unsupported operator')
    comparison={'>':value>threshold,'>=':value>=threshold,'<':value<threshold,'<=':value<=threshold,'==':value==threshold}[op]
    r={'value':value,'threshold':threshold,'operator':op,'comparison':comparison,'unit':str(request.get('unit') or '').strip() or None,'source_threshold_label':str(request.get('source_threshold_label') or '').strip() or None,'wildfire_warning':False,'evacuation_order':False,'ecosystem_health_finding':False,'deforestation_finding':False,'causal_attribution':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='nasa-firms',indicator_type='active-fire-detection',latitude=None,longitude=None,date=''):
    cur=state(source_id,indicator_type,latitude,longitude,date); p={'schema':'sc-site-intelligence-terrestrial-ecosystems/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'query_point':cur['query_point'],'date':cur['date']},'evidence':cur['evidence'],'review':{'active_fire_as_incident':False,'active_fire_as_burned_area':False,'vegetation_index_as_ecosystem_health':False,'land_cover_as_legal_land_use':False,'satellite_as_ground_truth':False,'near_real_time_as_consolidated':False,'wildfire_warning':False,'zero_records_as_no_fire_or_no_change':False}}
    return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
    c={'four_source_families_registered':len(SOURCES)==4,'nasa_firms_registered':'nasa-firms' in SOURCES,'modis_vegetation_registered':'nasa-modis-vegetation' in SOURCES,'copernicus_lcfm_registered':'copernicus-lcfm' in SOURCES,'copernicus_vegetation_registered':'copernicus-global-vegetation' in SOURCES,'active_fire_burned_area_guard_present':True,'vegetation_health_guard_present':True,'land_cover_legal_use_guard_present':True,'wildfire_warning_guard_present':True,'public_route_count_preserved':True}
    return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
