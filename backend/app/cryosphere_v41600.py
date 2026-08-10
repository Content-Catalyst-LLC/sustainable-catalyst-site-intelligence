from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-cryosphere-intelligence-frozen-earth-conditions'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'noaa-nsidc-sea-ice-index':{'title':'NOAA/NSIDC Sea Ice Index, Version 4','organization':'NOAA at NSIDC','url':'https://nsidc.org/data/g02135/versions/4','api_url':'https://noaadata.apps.nsidc.org/NOAA/G02135/','recognized_hosts':['nsidc.org','www.nsidc.org','noaadata.apps.nsidc.org'],'indicator_types':['sea-ice-extent','sea-ice-concentration','sea-ice-anomaly'],'evidence_classes':['satellite-derived','climatology'],'coverage':'Arctic and Antarctic daily/monthly sea-ice extent and concentration products with a long-term record beginning in 1978/1979.','limitations':'Sea Ice Index uses source-defined algorithms, concentration thresholds, reference periods and quality procedures. Near-real-time and final products must remain distinguishable, and missing cells are not interpreted as ice-free.'},
'nasa-nsidc-daac':{'title':'NASA NSIDC Distributed Active Archive Center','organization':'NASA NSIDC DAAC','url':'https://nsidc.org/data/data-programs/nsidc-daac','api_url':'https://cmr.earthdata.nasa.gov/search/collections.json','recognized_hosts':['nsidc.org','www.nsidc.org','cmr.earthdata.nasa.gov','earthdata.nasa.gov'],'indicator_types':['snow-cover','snow-depth','snow-water-equivalent','ice-sheet-elevation','ice-velocity','ice-thickness','freeze-thaw','frozen-ground'],'evidence_classes':['satellite-derived','airborne-observation','field-observation','model-analysis'],'coverage':'NASA cryosphere collections spanning snow, sea ice, ice sheets, glaciers, frozen ground and related geophysical measurements.','limitations':'Collection availability, authentication and processing levels vary by data set. A catalog hit is not an observation, and source processing level and temporal status remain visible.'},
'glims':{'title':'Global Land Ice Measurements from Space (GLIMS)','organization':'NSIDC DAAC / GLIMS initiative','url':'https://nsidc.org/data/glims','api_url':'https://cmr.earthdata.nasa.gov/search/collections.json?keyword=GLIMS','recognized_hosts':['nsidc.org','www.nsidc.org','cmr.earthdata.nasa.gov'],'indicator_types':['glacier-outline','glacier-area','snowline','supraglacial-lake'],'evidence_classes':['inventory-geometry','satellite-derived'],'coverage':'Global glacier inventory and repeat-survey attributes including glacier geometry, area, snowlines, lakes and debris context.','limitations':'Inventory geometry is timestamped source evidence. A mapped outline or area does not by itself establish current glacier position, mass balance, ice thickness, stability or hazard.'},
'modis-snow-sea-ice':{'title':'MODIS Snow & Sea Ice Products','organization':'NASA NSIDC DAAC','url':'https://nsidc.org/data/modis/data','api_url':'https://cmr.earthdata.nasa.gov/search/collections.json?keyword=MODIS%20snow%20sea%20ice','recognized_hosts':['nsidc.org','www.nsidc.org','cmr.earthdata.nasa.gov'],'indicator_types':['snow-cover','snow-albedo','sea-ice-cover','sea-ice-temperature'],'evidence_classes':['satellite-derived'],'coverage':'Global MODIS snow-cover and sea-ice products with product-specific spatial and temporal resolution.','limitations':'Clouds, sensor geometry, classification rules and data gaps affect optical/thermal products. Pixel classification is not a parcel-level surface condition or travel-safety determination.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('sea-ice-extent','Sea-ice extent','sea-ice'),('sea-ice-concentration','Sea-ice concentration','sea-ice'),('sea-ice-anomaly','Sea-ice anomaly','sea-ice'),('sea-ice-cover','Sea-ice cover','sea-ice'),('sea-ice-temperature','Sea-ice temperature','sea-ice'),('snow-cover','Snow cover','snow'),('snow-depth','Snow depth','snow'),('snow-water-equivalent','Snow-water equivalent','snow'),('snow-albedo','Snow albedo','snow'),('glacier-outline','Glacier outline','land-ice'),('glacier-area','Glacier area','land-ice'),('snowline','Snowline','land-ice'),('supraglacial-lake','Supraglacial lake','land-ice'),('ice-sheet-elevation','Ice-sheet elevation','land-ice'),('ice-velocity','Ice velocity','land-ice'),('ice-thickness','Ice thickness','land-ice'),('freeze-thaw','Freeze/thaw state','frozen-ground'),('frozen-ground','Frozen ground / permafrost context','frozen-ground')]}
EVIDENCE_CLASSES={'satellite-derived':'source-processed satellite measurement or classification','airborne-observation':'airborne instrument observation retained with campaign context','field-observation':'in-situ or field observation retained with source metadata','inventory-geometry':'source inventory geometry with observation/analysis date retained','model-analysis':'source-generated analysis or modeled field that is not converted to observation','climatology':'source-defined reference-period statistic or climatology'}
def _source(v):
    k=(v or 'noaa-nsidc-sea-ice-index').strip().lower()
    if k not in SOURCES: raise ValueError(f'unsupported cryosphere source: {k}')
    return k,{'id':k,**SOURCES[k]}
def _indicator(v):
    k=(v or 'sea-ice-extent').strip().lower()
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
def _bbox(v,field='bbox'):
    if v in (None,''): return None
    if not isinstance(v,(list,tuple)) or len(v)!=4: raise ValueError(f'{field} must be [west,south,east,north]')
    w,s,e,n=[float(x) for x in v]
    if not(-180<=w<=180 and -180<=e<=180 and -90<=s<=90 and -90<=n<=90): raise ValueError(f'{field} coordinates outside valid bounds')
    if w>e or s>n: raise ValueError(f'{field} must not cross antimeridian and must be ordered')
    return [round(w,6),round(s,6),round(e,6),round(n,6)]
def _url(source,raw):
    value=str(raw or '').strip(); p=urlparse(value)
    if p.scheme!='https' or (p.hostname or '').lower() not in source['recognized_hosts']: raise ValueError('source_url must use HTTPS and a registered source host')
    return value
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'summary':'Orient sea ice, snow, glaciers, ice sheets and frozen-ground evidence while keeping product status, resolution, processing and uncertainty visible.','warning':'CRYOSPHERE EVIDENCE · NOT A LOCAL SAFETY OR HAZARD DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'missing_data_means_no_ice_or_snow':False,'near_real_time_equals_final':False,'inventory_geometry_is_current_position':False,'glacier_outline_proves_mass_balance':False,'frozen_ground_map_proves_local_permafrost':False,'pixel_is_local_safety_determination':False,'model_analysis_is_observation':False}}
def state(source_id='noaa-nsidc-sea-ice-index',indicator_type='sea-ice-extent',latitude=None,longitude=None,date=''):
    _,source=_source(source_id); iid,indicator=_indicator(indicator_type)
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':source,'indicator_type':indicator,'query_point':_point(latitude,longitude),'date':str(date or '').strip() or None,'source_supports_indicator_type':iid in source['indicator_types'],'evidence':{'measurement_loaded':False,'feature_loaded':False,'climatology_loaded':False},'truth':{'near_real_time_treated_as_final':False,'missing_data_treated_as_no_ice_or_snow':False,'inventory_geometry_treated_as_current_position':False,'model_analysis_treated_as_observation':False,'local_safety_determination':False,'hazard_declaration':False,'travel_advice':False,'glacier_mass_balance_inferred':False,'local_permafrost_presence_inferred':False}}
def normalize_measurement(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id')); iid,indicator=_indicator(request.get('indicator_type'))
    if iid not in source['indicator_types']: raise ValueError('source does not register the requested cryosphere indicator')
    ev=_evidence(request.get('evidence_class') or 'satellite-derived')
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    value=request.get('value'); value=None if value in (None,'') else float(value)
    quality=str(request.get('quality_status') or '').strip() or None
    status=str(request.get('temporal_status') or '').strip().lower() or 'source-reported'
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'value':value,'unit':str(request.get('unit') or '').strip() or None,'observed_at':str(request.get('observed_at') or '').strip() or None,'temporal_status':status,'quality_status':quality,'query_point':_point(request.get('latitude'),request.get('longitude')),'near_real_time_treated_as_final':False,'missing_data_treated_as_zero':False,'model_analysis_treated_as_observation':False,'local_safety_determination':False,'hazard_declaration':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'measurement':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_feature(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id')); iid,indicator=_indicator(request.get('indicator_type'))
    if iid not in source['indicator_types']: raise ValueError('source does not register the requested cryosphere feature')
    ev=_evidence(request.get('evidence_class') or 'inventory-geometry')
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    bbox=_bbox(request.get('bbox'))
    if bbox is None: raise ValueError('feature record requires bbox')
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'feature_id':str(request.get('feature_id') or '').strip() or None,'bbox':bbox,'source_date':str(request.get('source_date') or '').strip() or None,'inventory_geometry_treated_as_current_position':False,'glacier_mass_balance_inferred':False,'ice_thickness_inferred':False,'local_permafrost_presence_inferred':False,'hazard_declaration':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'feature':r,'record_sha256':_digest(r),'normalized_at':_now()}
def anomaly_preview(request:dict[str,Any]):
    current=request.get('current_value'); baseline=request.get('baseline_value')
    if current in (None,'') or baseline in (None,''): raise ValueError('current_value and baseline_value are required')
    current,baseline=float(current),float(baseline); delta=current-baseline
    r={'current_value':current,'baseline_value':baseline,'delta':delta,'unit':str(request.get('unit') or '').strip() or None,'reference_period':str(request.get('reference_period') or '').strip() or None,'source_defined_baseline_required':True,'anomaly_is_hazard_declaration':False,'anomaly_is_local_safety_determination':False,'causal_attribution_inferred':False,'future_condition_predicted':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='noaa-nsidc-sea-ice-index',indicator_type='sea-ice-extent',latitude=None,longitude=None,date=''):
    cur=state(source_id,indicator_type,latitude,longitude,date); p={'schema':'sc-site-intelligence-cryosphere/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'query_point':cur['query_point'],'date':cur['date']},'evidence':cur['evidence'],'review':{'near_real_time_as_final':False,'missing_data_as_no_ice_or_snow':False,'inventory_geometry_as_current_position':False,'model_analysis_as_observation':False,'local_safety_determination':False,'hazard_declaration':False,'glacier_mass_balance_inferred':False,'local_permafrost_presence_inferred':False}}
    return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
    c={'four_source_families_registered':len(SOURCES)==4,'sea_ice_index_v4_registered':'noaa-nsidc-sea-ice-index' in SOURCES,'nasa_nsidc_daac_registered':'nasa-nsidc-daac' in SOURCES,'glims_registered':'glims' in SOURCES,'modis_registered':'modis-snow-sea-ice' in SOURCES,'near_real_time_final_guard_present':True,'missing_data_guard_present':True,'inventory_current_position_guard_present':True,'local_safety_guard_present':True,'public_route_count_preserved':True}
    return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
