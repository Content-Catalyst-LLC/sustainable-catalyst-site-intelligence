from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-agriculture-crops-food-system-conditions-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'faostat':{'title':'FAOSTAT Food & Agriculture Statistics','organization':'Food and Agriculture Organization of the United Nations','url':'https://www.fao.org/faostat/en/','api_url':'https://www.fao.org/faostat/en/','recognized_hosts':['www.fao.org','fao.org','faostat.fao.org'],'indicator_types':['crop-production','harvested-area','yield-statistic','food-balance-supply','producer-price-index'],'evidence_classes':['official-statistical-series','food-balance-statistical-series'],'coverage':'Global food and agriculture statistics for more than 245 countries and territories, including production, area, yield, food-balance and related statistical domains.','limitations':'FAOSTAT values are statistical observations/estimates reported through FAO statistical systems. They are not field-level measurements, real-time crop conditions, local harvest forecasts or independent food-security determinations.'},
'usda-nass-quick-stats':{'title':'USDA NASS Quick Stats','organization':'U.S. Department of Agriculture National Agricultural Statistics Service','url':'https://www.nass.usda.gov/Quick_Stats/','api_url':'https://quickstats.nass.usda.gov/api','recognized_hosts':['www.nass.usda.gov','nass.usda.gov','quickstats.nass.usda.gov','data.nass.usda.gov'],'indicator_types':['crop-production','harvested-area','yield-statistic','planted-area','inventory-statistic'],'evidence_classes':['survey-statistical-estimate','census-statistical-record'],'coverage':'Official U.S. agricultural estimates derived from NASS surveys and the Census of Agriculture, queryable by commodity, location and time period.','limitations':'NASS estimates are official statistical estimates, not exact field-by-field counts or direct observations at every location. Survey and census methodology, revision status and geographic aggregation must remain attached to the record.'},
'usda-crop-casma':{'title':'USDA Crop-CASMA & VegScape','organization':'USDA NASS / NASA','url':'https://www.nass.usda.gov/Research_and_Science/Crop-CASMA/','api_url':'https://nassgeo.csiss.gmu.edu/CropCASMA/','recognized_hosts':['www.nass.usda.gov','nass.usda.gov','nassgeo.csiss.gmu.edu'],'indicator_types':['soil-moisture-condition','ndvi','vegetation-condition','crop-mask-context'],'evidence_classes':['satellite-derived-condition-index','earth-observation-crop-context'],'coverage':'Conterminous U.S. crop vegetation and soil-moisture condition context derived from NASA SMAP and MODIS products, including NDVI-based vegetation condition.','limitations':'Crop-CASMA and VegScape are Earth-observation condition tools. Soil-moisture and vegetation indices are not direct yield measurements, crop-loss findings, field inspections or official production forecasts.'},
'geoglam-crop-monitor':{'title':'GEOGLAM Crop Monitor','organization':'GEOGLAM Crop Monitor community of practice','url':'https://www.cropmonitor.org/','api_url':'https://www.cropmonitor.org/archive','recognized_hosts':['www.cropmonitor.org','cropmonitor.org'],'indicator_types':['crop-condition-assessment','agroclimatic-driver','expected-yield-outcome-context','crop-calendar-context'],'evidence_classes':['multi-source-consensus-assessment','crop-condition-map-record'],'coverage':'Open monthly consensus assessments of crop conditions and drivers, supported by remote sensing, ground observations, field reports and national/regional experts.','limitations':'Crop Monitor condition classes and expected-outcome context are source-issued multi-source assessments. They are not Sustainable Catalyst forecasts, guaranteed yields, market advice, food-security declarations or farm-level inspections.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('crop-production','Crop production','agricultural-statistics'),('harvested-area','Harvested area','agricultural-statistics'),('yield-statistic','Yield statistic','agricultural-statistics'),('food-balance-supply','Food-balance supply','food-system-statistics'),('producer-price-index','Producer price index','food-system-statistics'),('planted-area','Planted area','agricultural-statistics'),('inventory-statistic','Agricultural inventory statistic','agricultural-statistics'),('soil-moisture-condition','Soil-moisture condition','earth-observation'),('ndvi','NDVI','earth-observation'),('vegetation-condition','Vegetation condition','earth-observation'),('crop-mask-context','Crop-mask context','earth-observation'),('crop-condition-assessment','Crop-condition assessment','crop-monitoring'),('agroclimatic-driver','Agroclimatic driver','crop-monitoring'),('expected-yield-outcome-context','Expected-yield outcome context','crop-monitoring'),('crop-calendar-context','Crop-calendar context','crop-monitoring')]}
EVIDENCE_CLASSES={
'official-statistical-series':'official/statistical series retaining source dimensions, units, aggregation and revision context',
'food-balance-statistical-series':'FAOSTAT food-balance statistical series; not a household food-security or nutrition measurement',
'survey-statistical-estimate':'NASS survey-derived statistical estimate; not an exact field count',
'census-statistical-record':'Census of Agriculture statistical record retaining census geography and period',
'satellite-derived-condition-index':'SMAP/MODIS-derived crop or soil condition index; not a direct yield measurement',
'earth-observation-crop-context':'Earth-observation crop-mask/vegetation context retaining pixel, temporal and processing limitations',
'multi-source-consensus-assessment':'GEOGLAM multi-source consensus assessment retaining report date, crop, geography and condition class',
'crop-condition-map-record':'source-issued crop-condition map record; not a Sustainable Catalyst forecast or farm inspection'}
def _source(v):
 k=(v or 'faostat').strip().lower()
 if k not in SOURCES: raise ValueError(f'unsupported agriculture source: {k}')
 return k,{'id':k,**SOURCES[k]}
def _indicator(v):
 k=(v or 'crop-production').strip().lower()
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
def _url(src,raw):
 value=str(raw or '').strip(); p=urlparse(value)
 if p.scheme!='https' or (p.hostname or '').lower() not in src['recognized_hosts']: raise ValueError('source_url must use HTTPS and a registered source host')
 return value
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'evidence_class_count':len(EVIDENCE_CLASSES),'summary':'Orient global and U.S. agricultural statistics, Earth-observation crop conditions and multi-source crop assessments while preserving statistical, remote-sensing, forecast and food-security boundaries.','warning':'AGRICULTURAL EVIDENCE · NOT A FIELD INSPECTION, PRODUCTION FORECAST OR FOOD-SECURITY DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'official_statistic_equals_field_observation':False,'statistical_estimate_equals_exact_count':False,'eo_condition_equals_yield_measurement':False,'crop_monitor_condition_equals_platform_forecast':False,'food_balance_equals_food_security_determination':False,'zero_records_equals_no_crop_or_no_stress':False,'platform_market_advice':False,'automatic_action_authorized':False}}
def state(source_id='faostat',indicator_type='crop-production',commodity='',area='',year='',latitude=None,longitude=None):
 _,src=_source(source_id); iid,ind=_indicator(indicator_type)
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':src,'indicator_type':ind,'commodity':str(commodity or '').strip() or None,'area':str(area or '').strip() or None,'year':str(year or '').strip() or None,'query_point':_point(latitude,longitude),'source_supports_indicator_type':iid in src['indicator_types'],'evidence':{'official_statistic_loaded':False,'earth_observation_condition_loaded':False,'crop_monitor_assessment_loaded':False,'field_observation_loaded':False,'food_security_assessment_loaded':False},'truth':{'official_statistic_treated_as_field_observation':False,'statistical_estimate_treated_as_exact_count':False,'eo_condition_treated_as_yield_measurement':False,'crop_monitor_condition_treated_as_platform_forecast':False,'food_balance_treated_as_food_security_determination':False,'zero_records_treated_as_no_crop_or_no_stress':False,'platform_market_advice_issued':False,'automatic_action_authorized':False}}
def normalize_measurement(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id')); iid,_=_indicator(request.get('indicator_type'))
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested agriculture indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'commodity':str(request.get('commodity') or '').strip() or None,'area':str(request.get('area') or '').strip() or None,'period':str(request.get('period') or request.get('year') or '').strip() or None,'value':None if request.get('value') in (None,'') else float(request.get('value')),'unit':str(request.get('unit') or '').strip() or None,'status_flag':str(request.get('status_flag') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'field_observation_inferred':False,'exact_count_inferred':False,'yield_measurement_inferred':False,'production_forecast_inferred':False,'food_security_determination_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'measurement':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_assessment(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'geoglam-crop-monitor'); iid,_=_indicator(request.get('indicator_type') or 'crop-condition-assessment')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested agriculture assessment')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 condition=str(request.get('condition') or '').strip().lower() or None
 allowed={None,'favourable','watch','poor','failure','exceptional','mixed','other'}
 if condition not in allowed: raise ValueError('unsupported crop condition class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'commodity':str(request.get('commodity') or '').strip() or None,'area':str(request.get('area') or '').strip() or None,'report_date':str(request.get('report_date') or '').strip() or None,'condition':condition,'driver':str(request.get('driver') or '').strip() or None,'source_issued_assessment':True,'platform_forecast_inferred':False,'guaranteed_yield_inferred':False,'food_security_declaration_inferred':False,'market_advice_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'assessment':r,'record_sha256':_digest(r),'normalized_at':_now()}
def threshold_preview(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 value=float(request.get('value')); threshold=float(request.get('threshold')); direction=str(request.get('direction') or 'below').strip().lower()
 if direction not in {'below','above'}: raise ValueError('direction must be below or above')
 crossed=value<threshold if direction=='below' else value>threshold
 r={'value':value,'threshold':threshold,'direction':direction,'threshold_crossed':crossed,'crop_loss_determined':False,'production_forecast_issued':False,'food_security_status_determined':False,'market_action_recommended':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='faostat',indicator_type='crop-production',commodity='',area='',year=''):
 cur=state(source_id,indicator_type,commodity,area,year); p={'schema':'sc-site-intelligence-agriculture-food/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'commodity':cur['commodity'],'area':cur['area'],'year':cur['year']},'evidence':cur['evidence'],'review':{'official_statistic_as_field_observation':False,'statistical_estimate_as_exact_count':False,'eo_condition_as_yield_measurement':False,'crop_condition_as_platform_forecast':False,'food_balance_as_food_security_determination':False,'zero_records_as_no_crop_or_stress':False,'platform_market_advice':False}}
 return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
 c={'four_source_families_registered':len(SOURCES)==4,'faostat_registered':'faostat' in SOURCES,'nass_quick_stats_registered':'usda-nass-quick-stats' in SOURCES,'crop_casma_registered':'usda-crop-casma' in SOURCES,'geoglam_registered':'geoglam-crop-monitor' in SOURCES,'statistical_field_observation_guard_present':True,'eo_yield_guard_present':True,'forecast_guard_present':True,'food_security_guard_present':True,'zero_result_guard_present':True,'public_route_count_preserved':True}
 return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
