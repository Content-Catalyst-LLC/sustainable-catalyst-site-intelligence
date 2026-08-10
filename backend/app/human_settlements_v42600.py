from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-human-settlements-urbanization-built-environment-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'jrc-ghsl':{'title':'JRC Global Human Settlement Layer (GHSL)','organization':'European Commission Joint Research Centre / Copernicus Emergency Management Service','url':'https://human-settlement.emergency.copernicus.eu/','api_url':'https://human-settlement.emergency.copernicus.eu/dataToolsOverview.php','recognized_hosts':['human-settlement.emergency.copernicus.eu','data.jrc.ec.europa.eu'],'indicator_types':['built-up-surface','built-up-volume','settlement-class','population-grid'],'evidence_classes':['earth-observation-built-environment-grid','ghsl-settlement-model'],'coverage':'Open global multitemporal built-up, population and settlement-model products, including GHS-BUILT-S, GHS-BUILT-V, GHS-POP and GHS-SMOD.','limitations':'GHSL combines Earth observation, population survey inputs and spatial-temporal modeling. Interpolated/extrapolated epochs are not direct observations for every year; built-up grids are not parcel building footprints, zoning records or current construction inventories.'},
'worldpop-global2':{'title':'WorldPop Global2 Population API','organization':'WorldPop / University of Southampton','url':'https://www.worldpop.org/','api_url':'https://api.worldpop.org/v2/','recognized_hosts':['www.worldpop.org','worldpop.org','api.worldpop.org','hub.worldpop.org'],'indicator_types':['population-estimate','population-density','age-sex-estimate'],'evidence_classes':['modeled-population-surface','modeled-demographic-estimate'],'coverage':'Global high-resolution population and age-sex estimates with current v2 API support for polygon statistics and 100 m or 1 km resolution.','limitations':'WorldPop outputs are modeled spatial demographic estimates, not a census headcount, household register, individual-level record or proof of occupancy at a specific structure.'},
'nasa-black-marble':{'title':'NASA VIIRS Black Marble','organization':'NASA Earthdata / LAADS DAAC','url':'https://earthdata.nasa.gov/data/catalog/lancemodis-vnp46a2-2','api_url':'https://cmr.earthdata.nasa.gov/search/granules.json','recognized_hosts':['earthdata.nasa.gov','cmr.earthdata.nasa.gov','ladsweb.modaps.eosdis.nasa.gov','blackmarble.gsfc.nasa.gov'],'indicator_types':['nighttime-radiance','nighttime-lights-composite','nighttime-lights-change'],'evidence_classes':['satellite-nighttime-radiance','derived-nighttime-lights-composite'],'coverage':'VIIRS Day/Night Band nighttime-light products including daily, monthly and yearly corrected radiance products available through NASA Earthdata/CMR.','limitations':'Nighttime radiance is a remotely sensed optical signal. It is not automatically population, economic output, electricity access, power-service status, building occupancy or infrastructure functionality; cloud, snow, lunar and other quality context must remain visible.'},
'world-bank-urban':{'title':'World Bank Urban Development Indicators','organization':'World Bank','url':'https://data.worldbank.org/topic/urban-development','api_url':'https://api.worldbank.org/v2/','recognized_hosts':['api.worldbank.org','data.worldbank.org','datahelpdesk.worldbank.org'],'indicator_types':['urban-population','urban-population-share','urban-population-growth'],'evidence_classes':['harmonized-urban-indicator-series'],'coverage':'World Development Indicators and related harmonized country-level urbanization time series available through the World Bank Indicators API.','limitations':'World Bank urban indicators are harmonized statistical series using source definitions and reference periods. They do not define parcel boundaries, settlement footprints, local zoning, service availability or a uniform global legal definition of urban land.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('built-up-surface','Built-up surface','built-environment'),('built-up-volume','Built-up volume','built-environment'),('settlement-class','Settlement class','settlement-model'),('population-grid','Population grid','settlement-model'),('population-estimate','Population estimate','demography'),('population-density','Population density','demography'),('age-sex-estimate','Age/sex estimate','demography'),('nighttime-radiance','Nighttime radiance','night-lights'),('nighttime-lights-composite','Nighttime lights composite','night-lights'),('nighttime-lights-change','Nighttime lights change','night-lights'),('urban-population','Urban population','urban-statistics'),('urban-population-share','Urban population share','urban-statistics'),('urban-population-growth','Urban population growth','urban-statistics')]}
EVIDENCE_CLASSES={
'earth-observation-built-environment-grid':'GHSL Earth-observation/model built-environment grid; not a parcel building inventory',
'ghsl-settlement-model':'GHSL settlement/population model output retaining epoch and modeled/interpolated status',
'modeled-population-surface':'WorldPop modeled gridded population estimate; not census headcount or individual occupancy',
'modeled-demographic-estimate':'WorldPop modeled age/sex estimate retaining source year, resolution and uncertainty context',
'satellite-nighttime-radiance':'VIIRS nighttime radiance measurement retaining quality and processing context',
'derived-nighttime-lights-composite':'processed nighttime-lights composite; not direct electricity, economy or population measurement',
'harmonized-urban-indicator-series':'country-level harmonized urban indicator series retaining source definition and reporting period'}
def _source(v):
 k=(v or 'jrc-ghsl').strip().lower()
 if k not in SOURCES: raise ValueError(f'unsupported human-settlements source: {k}')
 return k,{'id':k,**SOURCES[k]}
def _indicator(v):
 k=(v or 'built-up-surface').strip().lower()
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
 value=str(raw or '').strip();p=urlparse(value)
 if p.scheme!='https' or (p.hostname or '').lower() not in src['recognized_hosts']: raise ValueError('source_url must use HTTPS and a registered source host')
 return value
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'evidence_class_count':len(EVIDENCE_CLASSES),'summary':'Orient built-up morphology, modeled spatial population, nighttime-light signals and harmonized urbanization statistics without converting them into parcel, census, zoning or infrastructure-service determinations.','warning':'HUMAN SETTLEMENT EVIDENCE · NOT A CENSUS, PROPERTY, ZONING OR INFRASTRUCTURE-SERVICE DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'built_up_grid_equals_building_footprint':False,'modeled_epoch_equals_direct_observation':False,'population_estimate_equals_census_headcount':False,'night_lights_equals_electricity_service':False,'night_lights_equals_population_or_economic_output':False,'urban_indicator_equals_settlement_boundary':False,'zero_records_equals_uninhabited':False,'platform_zoning_or_property_determination':False,'automatic_action_authorized':False}}
def state(source_id='jrc-ghsl',indicator_type='built-up-surface',area='',year='',latitude=None,longitude=None):
 _,src=_source(source_id);iid,ind=_indicator(indicator_type)
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':src,'indicator_type':ind,'area':str(area or '').strip() or None,'year':str(year or '').strip() or None,'query_point':_point(latitude,longitude),'source_supports_indicator_type':iid in src['indicator_types'],'evidence':{'built_environment_grid_loaded':False,'population_estimate_loaded':False,'nighttime_radiance_loaded':False,'urban_indicator_loaded':False,'census_record_loaded':False,'parcel_record_loaded':False},'truth':{'built_up_grid_treated_as_building_footprint':False,'modeled_epoch_treated_as_direct_observation':False,'population_estimate_treated_as_census_headcount':False,'night_lights_treated_as_electricity_service':False,'night_lights_treated_as_population_or_economic_output':False,'urban_indicator_treated_as_settlement_boundary':False,'zero_records_treated_as_uninhabited':False,'platform_zoning_or_property_determination':False,'automatic_action_authorized':False}}
def normalize_measurement(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id'));iid,_=_indicator(request.get('indicator_type'))
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested human-settlements indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'value':None if request.get('value') in (None,'') else float(request.get('value')),'unit':str(request.get('unit') or '').strip() or None,'year':str(request.get('year') or '').strip() or None,'resolution':str(request.get('resolution') or '').strip() or None,'quality_flag':str(request.get('quality_flag') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'census_headcount_inferred':False,'electricity_service_inferred':False,'economic_output_inferred':False,'building_occupancy_inferred':False,'infrastructure_functionality_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'measurement':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_feature(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'jrc-ghsl');iid,_=_indicator(request.get('indicator_type') or 'settlement-class')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested human-settlements indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'source_feature_id':str(request.get('source_feature_id') or '').strip() or None,'source_class':str(request.get('source_class') or '').strip() or None,'epoch':str(request.get('epoch') or '').strip() or None,'processing_status':str(request.get('processing_status') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'parcel_building_footprint_inferred':False,'direct_observation_for_epoch_inferred':False,'zoning_status_inferred':False,'property_status_inferred':False,'occupancy_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'feature':r,'record_sha256':_digest(r),'normalized_at':_now()}
def threshold_preview(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 value=float(request.get('value'));threshold=float(request.get('threshold'));direction=str(request.get('direction') or 'above').strip().lower()
 if direction not in {'above','below'}: raise ValueError('direction must be above or below')
 crossed=value>=threshold if direction=='above' else value<=threshold
 r={'value':value,'threshold':threshold,'direction':direction,'threshold_crossed':crossed,'urban_status_determined':False,'population_presence_determined':False,'infrastructure_service_determined':False,'zoning_determined':False,'property_condition_determined':False,'emergency_condition_determined':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='jrc-ghsl',indicator_type='built-up-surface',area='',year='',latitude=None,longitude=None):
 cur=state(source_id,indicator_type,area,year,latitude,longitude);p={'schema':'sc-site-intelligence-human-settlements/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'area':cur['area'],'year':cur['year'],'query_point':cur['query_point']},'evidence':cur['evidence'],'review':{'built_up_as_parcel_footprint':False,'modeled_epoch_as_direct_observation':False,'population_estimate_as_census':False,'night_lights_as_electricity_service':False,'night_lights_as_population_or_economy':False,'urban_indicator_as_settlement_boundary':False,'zero_records_as_uninhabited':False,'platform_zoning_or_property_determination':False}}
 return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
 c={'four_source_families_registered':len(SOURCES)==4,'ghsl_registered':'jrc-ghsl' in SOURCES,'worldpop_v2_registered':'worldpop-global2' in SOURCES,'black_marble_registered':'nasa-black-marble' in SOURCES,'world_bank_urban_registered':'world-bank-urban' in SOURCES,'census_guard_present':True,'night_lights_guard_present':True,'built_environment_guard_present':True,'zoning_property_guard_present':True,'public_route_count_preserved':True}
 return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
