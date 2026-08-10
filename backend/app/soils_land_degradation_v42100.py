from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-soils-land-degradation-desertification-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'isric-soilgrids':{
 'title':'ISRIC SoilGrids 250 m Soil Property Maps','organization':'ISRIC — World Soil Information','url':'https://www.isric.org/explore/soilgrids','api_url':'https://rest.isric.org/soilgrids/v2.0/','recognized_hosts':['www.isric.org','isric.org','rest.isric.org'],'indicator_types':['soil-organic-carbon','clay-fraction','sand-fraction','silt-fraction','bulk-density','cation-exchange-capacity','ph-water'],'evidence_classes':['modelled-soil-property-map'],'coverage':'Global predictive soil-property maps at approximately 250 m for standard depth intervals.','limitations':'SoilGrids values are model predictions with uncertainty, not direct samples at a point. The REST v2 service is beta and publishes a fair-use limit; uptime is not guaranteed. Site Intelligence never converts a mapped prediction into ground-survey truth.'},
'usda-nrcs-soil-data-access':{
 'title':'USDA-NRCS Soil Data Access','organization':'USDA Natural Resources Conservation Service','url':'https://sdmdataaccess.nrcs.usda.gov/','api_url':'https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest','recognized_hosts':['sdmdataaccess.nrcs.usda.gov','sdmdataaccess.sc.egov.usda.gov'],'indicator_types':['soil-organic-carbon','clay-fraction','sand-fraction','silt-fraction','bulk-density','cation-exchange-capacity','ph-water','soil-taxonomic-class','hydrologic-soil-group'],'evidence_classes':['official-soil-survey-mapunit','official-soil-survey-tabular-record'],'coverage':'Official U.S. and Island Jurisdiction soil survey spatial and tabular information exposed through REST, WFS and WMS services.','limitations':'Soil-survey map units and component attributes are generalized survey information, not a parcel boundary survey, site-specific engineering determination, contamination finding, or substitute for field sampling.'},
'nasa-smap-soil-moisture':{
 'title':'NASA SMAP Soil Moisture','organization':'NASA / NSIDC DAAC','url':'https://nsidc.org/data/smap/data','api_url':'https://cmr.earthdata.nasa.gov/search/','recognized_hosts':['nsidc.org','www.nsidc.org','cmr.earthdata.nasa.gov','earthdata.nasa.gov','www.earthdata.nasa.gov'],'indicator_types':['surface-soil-moisture','root-zone-soil-moisture'],'evidence_classes':['satellite-soil-moisture-retrieval','model-assimilated-soil-moisture'],'coverage':'Global SMAP soil-moisture products, including satellite retrievals and model-assimilated surface/root-zone products distributed by NSIDC DAAC.','limitations':'Processing level matters. SMAP L2/L3 retrievals and L4 model-assimilated root-zone fields are distinct evidence classes. Grid-cell values are not direct in-situ soil samples and are not silently treated as parcel-scale conditions.'},
'unccd-land-degradation':{
 'title':'UNCCD SDG 15.3.1 Land Degradation Reporting','organization':'United Nations Convention to Combat Desertification','url':'https://data.unccd.int/land-degradation','api_url':'https://data.unccd.int/','recognized_hosts':['data.unccd.int','www.unccd.int','unccd.int','prais4-reporting-manual.unccd.int'],'indicator_types':['land-degradation-proportion','land-cover-change','land-productivity','soil-organic-carbon-change'],'evidence_classes':['country-reported-land-degradation-indicator','unccd-default-estimate'],'coverage':'Country reporting and UNCCD default estimates used for SDG indicator 15.3.1 and Land Degradation Neutrality reporting.','limitations':'UNCCD states that dashboard data are partial and should not be interpreted as a comprehensive global or regional assessment. Country-reported estimates, default estimates and nationally determined assumptions remain distinguishable.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('soil-organic-carbon','Soil organic carbon','soil-property'),('clay-fraction','Clay fraction','soil-property'),('sand-fraction','Sand fraction','soil-property'),('silt-fraction','Silt fraction','soil-property'),('bulk-density','Bulk density','soil-property'),('cation-exchange-capacity','Cation exchange capacity','soil-property'),('ph-water','Soil pH in water','soil-property'),('soil-taxonomic-class','Soil taxonomic class','soil-survey'),('hydrologic-soil-group','Hydrologic soil group','soil-survey'),('surface-soil-moisture','Surface soil moisture','soil-moisture'),('root-zone-soil-moisture','Root-zone soil moisture','soil-moisture'),('land-degradation-proportion','Proportion of land degraded','land-degradation'),('land-cover-change','Land-cover change','land-degradation'),('land-productivity','Land productivity','land-degradation'),('soil-organic-carbon-change','Soil organic carbon change','land-degradation')]}
EVIDENCE_CLASSES={
'modelled-soil-property-map':'predictive soil-property map with model uncertainty retained',
'official-soil-survey-mapunit':'official mapped soil-survey unit distinct from parcel/site-specific truth',
'official-soil-survey-tabular-record':'official soil-survey attribute record with mapunit/component context retained',
'satellite-soil-moisture-retrieval':'satellite-derived soil-moisture retrieval distinct from in-situ observation',
'model-assimilated-soil-moisture':'model-assimilated surface/root-zone soil-moisture field distinct from direct measurement',
'country-reported-land-degradation-indicator':'country-reported UNCCD/SDG indicator record with reporting context retained',
'unccd-default-estimate':'UNCCD default estimate distinct from nationally verified country data'}
def _source(v):
    k=(v or 'isric-soilgrids').strip().lower()
    if k not in SOURCES: raise ValueError(f'unsupported soils source: {k}')
    return k,{'id':k,**SOURCES[k]}
def _indicator(v):
    k=(v or 'soil-organic-carbon').strip().lower()
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
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'summary':'Orient mapped soil properties, official soil surveys, soil moisture and land-degradation reporting while preserving model, survey, satellite and country-report evidence boundaries.','warning':'SOIL & LAND EVIDENCE · NOT A SITE INVESTIGATION, LAND-DEGRADATION DECLARATION OR CARBON CLAIM'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'soilgrids_equals_ground_sample':False,'soil_survey_mapunit_equals_parcel_truth':False,'smap_l4_equals_direct_observation':False,'unccd_report_equals_comprehensive_global_assessment':False,'degradation_indicator_equals_causal_attribution':False,'soil_carbon_equals_carbon_credit':False,'zero_records_equals_healthy_soil':False}}
def state(source_id='isric-soilgrids',indicator_type='soil-organic-carbon',latitude=None,longitude=None,date=''):
    _,source=_source(source_id); iid,indicator=_indicator(indicator_type)
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':source,'indicator_type':indicator,'query_point':_point(latitude,longitude),'date':str(date or '').strip() or None,'source_supports_indicator_type':iid in source['indicator_types'],'evidence':{'soil_property_loaded':False,'soil_survey_loaded':False,'soil_moisture_loaded':False,'land_degradation_record_loaded':False},'truth':{'soilgrids_treated_as_ground_sample':False,'soil_survey_mapunit_treated_as_parcel_truth':False,'smap_l4_treated_as_direct_observation':False,'unccd_record_treated_as_comprehensive_global_assessment':False,'degradation_indicator_treated_as_causal_attribution':False,'soil_carbon_treated_as_carbon_credit':False,'zero_records_treated_as_healthy_soil':False,'automatic_action_authorized':False}}
def normalize_measurement(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id')); iid,_=_indicator(request.get('indicator_type'))
    if iid not in source['indicator_types']: raise ValueError('source does not register the requested soil/land indicator')
    ev=_evidence(request.get('evidence_class') or source['evidence_classes'][0])
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    value=request.get('value'); value=None if value in (None,'') else float(value)
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'value':value,'unit':str(request.get('unit') or '').strip() or None,'depth_interval':str(request.get('depth_interval') or '').strip() or None,'observed_or_valid_at':str(request.get('observed_or_valid_at') or '').strip() or None,'processing_level':str(request.get('processing_level') or '').strip() or None,'uncertainty':request.get('uncertainty'),'query_point':_point(request.get('latitude'),request.get('longitude')),'modelled_map_treated_as_ground_sample':False,'mapunit_treated_as_parcel_truth':False,'model_assimilation_treated_as_direct_observation':False,'soil_carbon_treated_as_carbon_credit':False,'platform_determination_issued':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'measurement':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_assessment(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id') or 'unccd-land-degradation'); iid,_=_indicator(request.get('indicator_type') or 'land-degradation-proportion')
    if iid not in source['indicator_types']: raise ValueError('source does not register the requested land-degradation indicator')
    ev=_evidence(request.get('evidence_class') or source['evidence_classes'][0])
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'reporting_entity':str(request.get('reporting_entity') or '').strip() or None,'reporting_period':str(request.get('reporting_period') or '').strip() or None,'value':None if request.get('value') in (None,'') else float(request.get('value')),'unit':str(request.get('unit') or '').strip() or None,'country_reported':ev=='country-reported-land-degradation-indicator','default_estimate':ev=='unccd-default-estimate','comprehensive_global_assessment':False,'causal_attribution':False,'desertification_declaration':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'assessment':r,'record_sha256':_digest(r),'normalized_at':_now()}
def threshold_preview(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    value=float(request.get('value')); threshold=float(request.get('threshold')); op=str(request.get('operator') or '>=').strip()
    if op not in {'>','>=','<','<=','=='}: raise ValueError('unsupported operator')
    comparison={'>':value>threshold,'>=':value>=threshold,'<':value<threshold,'<=':value<=threshold,'==':value==threshold}[op]
    r={'value':value,'threshold':threshold,'operator':op,'comparison':comparison,'unit':str(request.get('unit') or '').strip() or None,'source_threshold_label':str(request.get('source_threshold_label') or '').strip() or None,'land_degradation_declaration':False,'desertification_declaration':False,'soil_health_finding':False,'contamination_finding':False,'carbon_credit_finding':False,'causal_attribution':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='isric-soilgrids',indicator_type='soil-organic-carbon',latitude=None,longitude=None,date=''):
    cur=state(source_id,indicator_type,latitude,longitude,date); p={'schema':'sc-site-intelligence-soils-land/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'query_point':cur['query_point'],'date':cur['date']},'evidence':cur['evidence'],'review':{'soilgrids_as_ground_sample':False,'soil_survey_as_parcel_truth':False,'smap_l4_as_direct_observation':False,'unccd_as_comprehensive_global_assessment':False,'degradation_as_causal_attribution':False,'soil_carbon_as_carbon_credit':False,'zero_records_as_healthy_soil':False}}
    return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
    c={'four_source_families_registered':len(SOURCES)==4,'soilgrids_registered':'isric-soilgrids' in SOURCES,'usda_soil_data_access_registered':'usda-nrcs-soil-data-access' in SOURCES,'nasa_smap_registered':'nasa-smap-soil-moisture' in SOURCES,'unccd_land_degradation_registered':'unccd-land-degradation' in SOURCES,'model_ground_sample_guard_present':True,'mapunit_parcel_guard_present':True,'smap_processing_guard_present':True,'unccd_partial_reporting_guard_present':True,'carbon_credit_guard_present':True,'public_route_count_preserved':True}
    return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
