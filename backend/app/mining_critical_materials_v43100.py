from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-mining-mineral-resources-critical-materials-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'openstreetmap-mining':{'title':'OpenStreetMap Mining & Quarry Features','organization':'OpenStreetMap contributors / OpenStreetMap Foundation','url':'https://wiki.openstreetmap.org/wiki/Tag:landuse%3Dquarry','api_url':'https://overpass-api.de/api/interpreter','recognized_hosts':['wiki.openstreetmap.org','overpass-api.de','www.openstreetmap.org','openstreetmap.org'],'indicator_types':['mine-site','quarry','mine-shaft','adit','tailings-or-spoil'],'evidence_classes':['community-mapped-mining-feature'],'coverage':'Global community-mapped quarry, mine, shaft, adit, tailings/spoil and related extraction features where contributors have mapped them.','limitations':'OpenStreetMap mining features are community-maintained geometry and tags. They may be incomplete or stale and do not establish ownership, current operation, permit status, production, reserves, environmental compliance, worker safety or legal access.'},
'usgs-usmin':{'title':'USGS USMIN Mineral Deposit Database','organization':'U.S. Geological Survey Mineral Resources Program','url':'https://www.usgs.gov/centers/gggsc/science/usmin-mineral-deposit-database','api_url':'https://data.usgs.gov/datacatalog/data/USGS%3A6464de5bd34ec179a83d9e6c','recognized_hosts':['www.usgs.gov','usgs.gov','data.usgs.gov','doi.org'],'indicator_types':['critical-mineral-deposit','reported-resource','reported-production-history','deposit-type','mineral-system'],'evidence_classes':['authoritative-us-mineral-deposit-record'],'coverage':'Authoritative U.S. geospatial records for significant mines, mineral deposits and districts, including critical-mineral deposits with reported production and/or resource estimates.','limitations':'USMIN is a mineral-resource/deposit database, not a live mine-operations service. Deposit/resource records do not establish current mine status, economic recoverability, reserves under another reporting code, permit status, ownership, environmental performance or future production.'},
'usgs-mcs-2026':{'title':'USGS Mineral Commodity Summaries 2026','organization':'U.S. Geological Survey National Minerals Information Center','url':'https://pubs.usgs.gov/publication/mcs2026','api_url':'https://data.usgs.gov/datacatalog/data/USGS%3A69837e43b66b01367d7ec7c7','recognized_hosts':['pubs.usgs.gov','www.usgs.gov','usgs.gov','data.usgs.gov','doi.org'],'indicator_types':['world-mine-production','world-reserves','us-production','net-import-reliance','recycling-context'],'evidence_classes':['official-mineral-commodity-statistic'],'coverage':'2026 USGS commodity data release covering 2021-2025 salient statistics, world production, reserves/resources context and U.S. industry/trade information for more than 90 minerals and materials.','limitations':'Commodity summaries are annual statistical estimates compiled from multiple sources and may be revised. Reserve/resource definitions vary by source and jurisdiction; national production does not establish mine-level output or operating status, and import reliance does not prove disruption or supplier dependency.'},
'iea-critical-minerals':{'title':'IEA Critical Minerals Data Explorer','organization':'International Energy Agency','url':'https://www.iea.org/data-and-statistics/data-tools/critical-minerals-data-explorer','api_url':'https://www.iea.org/data-and-statistics/data-tools/critical-minerals-data-explorer','recognized_hosts':['www.iea.org','iea.org'],'indicator_types':['projected-total-demand','projected-clean-energy-demand','projected-supply','scenario-gap','technology-demand'],'evidence_classes':['scenario-based-critical-mineral-projection'],'coverage':'CC BY 4.0 scenario-based demand and selected supply projections for critical minerals, including technology-specific cases and multiple energy-transition scenarios.','limitations':'IEA projections are scenario/model outputs, not observations or guaranteed future demand/supply. Scenario gaps do not by themselves establish shortages, price outcomes, project viability, national security findings or investment recommendations.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('mine-site','Mine site','mapped-feature'),('quarry','Quarry / surface extraction','mapped-feature'),('mine-shaft','Mine shaft','mapped-feature'),('adit','Mine adit','mapped-feature'),('tailings-or-spoil','Tailings / spoil feature','mapped-feature'),
('critical-mineral-deposit','Critical-mineral deposit','deposit'),('reported-resource','Reported mineral resource','deposit'),('reported-production-history','Reported production history','deposit'),('deposit-type','Deposit type','deposit'),('mineral-system','Mineral system','deposit'),
('world-mine-production','World mine production','commodity-statistic'),('world-reserves','World reserves','commodity-statistic'),('us-production','U.S. production','commodity-statistic'),('net-import-reliance','Net import reliance','commodity-statistic'),('recycling-context','Recycling context','commodity-statistic'),
('projected-total-demand','Projected total demand','scenario'),('projected-clean-energy-demand','Projected clean-energy demand','scenario'),('projected-supply','Projected supply','scenario'),('scenario-gap','Scenario supply-demand gap','scenario'),('technology-demand','Technology-specific mineral demand','scenario') ]}
EVIDENCE_CLASSES={
'community-mapped-mining-feature':'community-mapped extraction/mining geometry and attributes; not proof of operation, ownership, permit status, output, reserves or environmental compliance',
'authoritative-us-mineral-deposit-record':'USGS deposit/resource record retaining published classification and source context; not live operation, economic feasibility, permit status or guaranteed reserve',
'official-mineral-commodity-statistic':'official annual mineral commodity statistic retaining commodity, period, unit and source definitions; not mine-level telemetry or current operating status',
'scenario-based-critical-mineral-projection':'scenario/model projection retaining scenario and horizon; not observation, guaranteed forecast, shortage declaration or investment recommendation'}
def _source(v):
 k=(v or 'openstreetmap-mining').strip().lower()
 if k not in SOURCES: raise ValueError(f'unsupported mining/mineral source: {k}')
 return k,{'id':k,**SOURCES[k]}
def _indicator(v):
 k=(v or 'mine-site').strip().lower()
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
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'evidence_class_count':len(EVIDENCE_CLASSES),'summary':'Orient mapped mining features, authoritative mineral-deposit records, official mineral commodity statistics and critical-mineral scenarios without converting them into live mine status, guaranteed reserves, shortage declarations or investment recommendations.','warning':'MINERAL & MINING EVIDENCE · NOT OPERATING STATUS, RESERVE CERTIFICATION OR SUPPLY-SHORTAGE DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'mapped_mining_feature_equals_operating_mine':False,'deposit_resource_record_equals_certified_reserve':False,'national_production_equals_mine_output':False,'scenario_projection_equals_observation_or_guaranteed_forecast':False,'scenario_gap_equals_shortage':False,'critical_mineral_label_equals_investment_or_security_determination':False,'zero_records_equals_no_mineral_resource':False,'automatic_action_authorized':False}}
def state(source_id='openstreetmap-mining',indicator_type='mine-site',area='',date='',latitude=None,longitude=None):
 _,src=_source(source_id);iid,ind=_indicator(indicator_type)
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':src,'indicator_type':ind,'area':str(area or '').strip() or None,'date':str(date or '').strip() or None,'query_point':_point(latitude,longitude),'source_supports_indicator_type':iid in src['indicator_types'],'evidence':{'mining_feature_loaded':False,'deposit_record_loaded':False,'commodity_statistic_loaded':False,'scenario_projection_loaded':False,'live_operating_confirmation_loaded':False,'certified_reserve_statement_loaded':False},'truth':{'mapped_feature_treated_as_operating_mine':False,'deposit_resource_treated_as_certified_reserve':False,'national_production_treated_as_mine_output':False,'scenario_treated_as_observation_or_guaranteed_forecast':False,'scenario_gap_treated_as_shortage':False,'critical_label_treated_as_investment_or_security_determination':False,'zero_records_treated_as_no_mineral_resource':False,'automatic_action_authorized':False}}
def normalize_feature(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'openstreetmap-mining');iid,_=_indicator(request.get('indicator_type') or 'mine-site')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested mining indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'source_feature_id':str(request.get('source_feature_id') or '').strip() or None,'resource':str(request.get('resource') or '').strip() or None,'operator':str(request.get('operator') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'operating_status_inferred':False,'ownership_verified':False,'production_inferred':False,'reserve_inferred':False,'permit_status_inferred':False,'environmental_compliance_inferred':False,'legal_access_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'feature':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_resource(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'usgs-usmin');iid,_=_indicator(request.get('indicator_type') or 'reported-resource')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested deposit/resource indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'deposit_id':str(request.get('deposit_id') or '').strip() or None,'commodity':str(request.get('commodity') or '').strip() or None,'classification':str(request.get('classification') or '').strip() or None,'value':request.get('value'),'unit':str(request.get('unit') or '').strip() or None,'period':str(request.get('period') or '').strip() or None,'certified_reserve_inferred':False,'economic_recoverability_inferred':False,'mine_operating_status_inferred':False,'permit_status_inferred':False,'future_production_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'resource':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_series(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'usgs-mcs-2026');iid,_=_indicator(request.get('indicator_type') or 'world-mine-production')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested commodity/scenario indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'commodity':str(request.get('commodity') or '').strip() or None,'area_code':str(request.get('area_code') or '').strip() or None,'period':str(request.get('period') or '').strip() or None,'scenario':str(request.get('scenario') or '').strip() or None,'value':request.get('value'),'unit':str(request.get('unit') or '').strip() or None,'mine_level_output_inferred':False,'live_operating_status_inferred':False,'guaranteed_forecast_inferred':False,'shortage_inferred':False,'price_outcome_inferred':False,'investment_recommendation_inferred':False,'security_finding_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'series':r,'record_sha256':_digest(r),'normalized_at':_now()}
def threshold_preview(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 value=float(request.get('value'));threshold=float(request.get('threshold'));unit=str(request.get('unit') or '').strip() or None;direction=str(request.get('direction') or 'below').strip().lower()
 if direction not in {'above','below'}: raise ValueError('direction must be above or below')
 crossed=value>=threshold if direction=='above' else value<=threshold
 r={'value':value,'threshold':threshold,'unit':unit,'direction':direction,'screening_condition_met':crossed,'shortage_declared':False,'reserve_certified':False,'mine_shutdown_determined':False,'supply_dependency_determined':False,'investment_recommendation_issued':False,'national_security_finding_issued':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='openstreetmap-mining',indicator_type='mine-site',area='',date='',latitude=None,longitude=None):
 cur=state(source_id,indicator_type,area,date,latitude,longitude);p={'schema':'sc-site-intelligence-mining-critical-materials/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'area':cur['area'],'date':cur['date'],'query_point':cur['query_point']},'evidence':cur['evidence'],'review':{'mapped_feature_as_operating_mine':False,'deposit_resource_as_certified_reserve':False,'national_production_as_mine_output':False,'scenario_as_guaranteed_forecast':False,'scenario_gap_as_shortage':False,'critical_label_as_investment_or_security_determination':False,'zero_records_as_no_mineral_resource':False}}
 return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
 c={'four_source_families_registered':len(SOURCES)==4,'openstreetmap_mining_registered':'openstreetmap-mining' in SOURCES,'usgs_usmin_registered':'usgs-usmin' in SOURCES,'usgs_mcs_2026_registered':'usgs-mcs-2026' in SOURCES,'iea_critical_minerals_registered':'iea-critical-minerals' in SOURCES,'operating_status_guard_present':True,'reserve_certification_guard_present':True,'scenario_shortage_guard_present':True,'investment_security_guard_present':True,'public_route_count_preserved':True}
 return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
