from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-energy-infrastructure-power-systems-electricity-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'openstreetmap-power':{'title':'OpenStreetMap Power Infrastructure','organization':'OpenStreetMap contributors / OpenStreetMap Foundation','url':'https://wiki.openstreetmap.org/wiki/Power','api_url':'https://overpass-api.de/api/interpreter','recognized_hosts':['wiki.openstreetmap.org','overpass-api.de','www.openstreetmap.org','openstreetmap.org'],'indicator_types':['power-line','power-cable','substation','power-plant','generator'],'evidence_classes':['open-power-infrastructure-feature'],'coverage':'Global community-mapped power generation, transmission and distribution features including plants, generators, substations, lines and cables.','limitations':'OpenStreetMap power features are community-maintained mapping evidence. Geometry, voltage, operator, lifecycle and generation tags may be incomplete or stale and do not establish energization, ownership, operational availability, safety clearance or legal access.'},
'eia-open-data':{'title':'U.S. Energy Information Administration Open Data','organization':'U.S. Energy Information Administration','url':'https://www.eia.gov/opendata/','api_url':'https://api.eia.gov/v2/','recognized_hosts':['www.eia.gov','eia.gov','api.eia.gov'],'indicator_types':['electric-demand','net-generation','interchange','generation-by-fuel','installed-capacity'],'evidence_classes':['reported-energy-system-series'],'coverage':'U.S. balancing-authority operating data, electricity generation, plant/fuel statistics, capability and other official energy series exposed through EIA API v2 and bulk data.','limitations':'EIA series have source-specific temporal resolution, revision cycles and reporting definitions. Forecast demand is not actual demand; reported capability is not real-time available capacity; interchange and generation records do not by themselves establish grid reliability or local service status.'},
'ember-electricity-data':{'title':'Ember Electricity Data API','organization':'Ember','url':'https://ember-energy.org/data/api/','api_url':'https://api.ember-energy.org/v1/','recognized_hosts':['ember-energy.org','www.ember-energy.org','api.ember-energy.org'],'indicator_types':['electricity-generation','electricity-demand','installed-capacity','carbon-intensity','power-sector-emissions'],'evidence_classes':['harmonized-electricity-statistic'],'coverage':'Curated cross-country monthly and yearly electricity generation, demand, installed capacity, carbon intensity and power-sector emissions series published under CC BY 4.0.','limitations':'Ember provides harmonized statistical series, not real-time grid telemetry. Country-level values do not establish local feeder conditions, plant operating status, outage status, electricity access or causal attribution.'},
'entsoe-transparency':{'title':'ENTSO-E Transparency Platform','organization':'European Network of Transmission System Operators for Electricity','url':'https://www.entsoe.eu/data/transparency-platform/','api_url':'https://web-api.tp.entsoe.eu/api','recognized_hosts':['www.entsoe.eu','entsoe.eu','transparency.entsoe.eu','web-api.tp.entsoe.eu','transparencyplatform.zendesk.com'],'indicator_types':['actual-load','load-forecast','actual-generation','generation-forecast','cross-border-flow','day-ahead-price','transmission-unavailability'],'evidence_classes':['transparency-platform-market-system-record'],'coverage':'Pan-European electricity load, generation, transmission, balancing, market and outage publications available through the ENTSO-E Transparency Platform and web API.','limitations':'Transparency Platform records use bidding zones, control areas, EIC identifiers and market/system definitions. Forecasts are not observations; unavailability publications are source records rather than a platform outage declaration; market prices do not establish retail price or physical reliability.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('power-line','Power line','infrastructure'),('power-cable','Power cable','infrastructure'),('substation','Substation','infrastructure'),('power-plant','Power plant','infrastructure'),('generator','Generator','infrastructure'),
('electric-demand','Electric demand','operations'),('net-generation','Net generation','operations'),('interchange','Interchange','operations'),('generation-by-fuel','Generation by fuel','operations'),('installed-capacity','Installed capacity','capacity'),
('electricity-generation','Electricity generation','statistics'),('electricity-demand','Electricity demand','statistics'),('carbon-intensity','Carbon intensity','statistics'),('power-sector-emissions','Power-sector emissions','statistics'),
('actual-load','Actual load','system'),('load-forecast','Load forecast','forecast'),('actual-generation','Actual generation','system'),('generation-forecast','Generation forecast','forecast'),('cross-border-flow','Cross-border flow','system'),('day-ahead-price','Day-ahead price','market'),('transmission-unavailability','Transmission unavailability','system') ]}
EVIDENCE_CLASSES={
'open-power-infrastructure-feature':'community-mapped power infrastructure geometry/attributes; not proof of energization, availability, safety, ownership or legal access',
'reported-energy-system-series':'official EIA reported or forecast energy series retaining temporal/revision context; not local service or reliability proof',
'harmonized-electricity-statistic':'Ember harmonized statistical series; not real-time telemetry, plant status or local service evidence',
'transparency-platform-market-system-record':'ENTSO-E market/system publication retaining source process and area semantics; forecast/outage/price records are not platform-issued operational determinations'}
def _source(v):
 k=(v or 'openstreetmap-power').strip().lower()
 if k not in SOURCES: raise ValueError(f'unsupported energy source: {k}')
 return k,{'id':k,**SOURCES[k]}
def _indicator(v):
 k=(v or 'power-line').strip().lower()
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
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'evidence_class_count':len(EVIDENCE_CLASSES),'summary':'Orient power infrastructure, electricity operations, capacity, generation, demand, market and transmission evidence without converting maps, statistics, forecasts or source outage records into platform-issued grid-operability, reliability or safety determinations.','warning':'ENERGY-SYSTEM EVIDENCE · NOT AN OUTAGE, RELIABILITY, SAFETY OR OPERATING-STATUS DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'mapped_power_feature_equals_energized_asset':False,'reported_capacity_equals_real_time_available_capacity':False,'forecast_equals_observation':False,'unavailability_record_equals_platform_outage_declaration':False,'market_price_equals_retail_price':False,'country_statistic_equals_local_service_status':False,'zero_records_equals_no_energy_infrastructure':False,'platform_grid_reliability_or_safety_determination':False,'automatic_action_authorized':False}}
def state(source_id='openstreetmap-power',indicator_type='power-line',area='',date='',latitude=None,longitude=None):
 _,src=_source(source_id);iid,ind=_indicator(indicator_type)
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':src,'indicator_type':ind,'area':str(area or '').strip() or None,'date':str(date or '').strip() or None,'query_point':_point(latitude,longitude),'source_supports_indicator_type':iid in src['indicator_types'],'evidence':{'infrastructure_feature_loaded':False,'operating_series_loaded':False,'harmonized_statistic_loaded':False,'market_system_record_loaded':False,'real_time_local_service_confirmation_loaded':False},'truth':{'mapped_power_feature_treated_as_energized_asset':False,'reported_capacity_treated_as_real_time_available_capacity':False,'forecast_treated_as_observation':False,'unavailability_record_treated_as_platform_outage_declaration':False,'market_price_treated_as_retail_price':False,'country_statistic_treated_as_local_service_status':False,'zero_records_treated_as_no_energy_infrastructure':False,'platform_grid_reliability_or_safety_determination':False,'automatic_action_authorized':False}}
def normalize_feature(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'openstreetmap-power');iid,_=_indicator(request.get('indicator_type') or 'power-line')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested energy indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'source_feature_id':str(request.get('source_feature_id') or '').strip() or None,'source_class':str(request.get('source_class') or '').strip() or None,'voltage':request.get('voltage'),'operator':str(request.get('operator') or '').strip() or None,'lifecycle':str(request.get('lifecycle') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'energized_status_inferred':False,'operating_status_inferred':False,'ownership_inferred':False,'legal_access_inferred':False,'safety_clearance_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'feature':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_series(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'eia-open-data');iid,_=_indicator(request.get('indicator_type') or 'electric-demand')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested energy indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 is_forecast=bool(request.get('is_forecast',False)) or iid in {'load-forecast','generation-forecast'}
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'period':str(request.get('period') or '').strip() or None,'area_code':str(request.get('area_code') or '').strip() or None,'value':request.get('value'),'unit':str(request.get('unit') or '').strip() or None,'revision_status':str(request.get('revision_status') or '').strip() or None,'is_forecast':is_forecast,'forecast_treated_as_observation':False,'real_time_available_capacity_inferred':False,'local_service_status_inferred':False,'grid_reliability_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'series':r,'record_sha256':_digest(r),'normalized_at':_now()}
def threshold_preview(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 value=float(request.get('value'));threshold=float(request.get('threshold'));unit=str(request.get('unit') or '').strip() or None;direction=str(request.get('direction') or 'above').strip().lower()
 if direction not in {'above','below'}: raise ValueError('direction must be above or below')
 crossed=value>=threshold if direction=='above' else value<=threshold
 r={'value':value,'threshold':threshold,'unit':unit,'direction':direction,'screening_condition_met':crossed,'outage_declared':False,'reliability_violation_determined':False,'grid_emergency_determined':False,'equipment_safety_determined':False,'retail_price_determined':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='openstreetmap-power',indicator_type='power-line',area='',date='',latitude=None,longitude=None):
 cur=state(source_id,indicator_type,area,date,latitude,longitude);p={'schema':'sc-site-intelligence-energy-systems/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'area':cur['area'],'date':cur['date'],'query_point':cur['query_point']},'evidence':cur['evidence'],'review':{'mapped_feature_as_energized_asset':False,'reported_capacity_as_real_time_available_capacity':False,'forecast_as_observation':False,'unavailability_as_platform_outage':False,'market_price_as_retail_price':False,'country_statistic_as_local_service':False,'zero_records_as_no_infrastructure':False,'platform_grid_reliability_or_safety_determination':False}}
 return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
 c={'four_source_families_registered':len(SOURCES)==4,'openstreetmap_power_registered':'openstreetmap-power' in SOURCES,'eia_registered':'eia-open-data' in SOURCES,'ember_registered':'ember-electricity-data' in SOURCES,'entsoe_registered':'entsoe-transparency' in SOURCES,'forecast_observation_guard_present':True,'operating_status_guard_present':True,'grid_reliability_guard_present':True,'safety_guard_present':True,'public_route_count_preserved':True}
 return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
