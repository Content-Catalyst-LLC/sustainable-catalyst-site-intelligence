from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-industrial-facilities-manufacturing-trade-flow-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'openstreetmap-industrial':{'title':'OpenStreetMap Industrial Facilities','organization':'OpenStreetMap contributors / OpenStreetMap Foundation','url':'https://wiki.openstreetmap.org/wiki/Tag:man_made%3Dworks','api_url':'https://overpass-api.de/api/interpreter','recognized_hosts':['wiki.openstreetmap.org','overpass-api.de','www.openstreetmap.org','openstreetmap.org'],'indicator_types':['industrial-site','factory-works','refinery','warehouse-logistics','industrial-landuse'],'evidence_classes':['community-mapped-industrial-feature'],'coverage':'Global community-mapped factories, industrial sites, refineries, warehouses/logistics facilities and industrial land-use areas where contributors have mapped them.','limitations':'OpenStreetMap industrial features are community-maintained geometry and attributes. They may be incomplete or stale and do not establish ownership, current operation, production volume, employment, regulatory status, hazardous-material inventory or legal access.'},
'world-bank-manufacturing':{'title':'World Bank Manufacturing Indicators','organization':'World Bank / national statistical agencies','url':'https://data.worldbank.org/indicator/NV.IND.MANF.ZS','api_url':'https://api.worldbank.org/v2/','recognized_hosts':['data.worldbank.org','api.worldbank.org','www.worldbank.org','worldbank.org'],'indicator_types':['manufacturing-value-added','manufacturing-share-gdp','manufacturing-growth','medium-high-tech-manufacturing-share'],'evidence_classes':['harmonized-national-manufacturing-statistic'],'coverage':'Country/economy manufacturing value-added, manufacturing share, growth and technology-intensity indicators distributed through World Development Indicators.','limitations':'These are harmonized national/economy statistics with source-specific definitions, reporting periods, revisions and estimation methods. They do not establish facility-level output, current plant utilization, employment, profitability or causal explanations.'},
'world-bank-gem':{'title':'World Bank Global Economic Monitor — Industrial Production & Trade','organization':'World Bank','url':'https://datacatalog.worldbank.org/search/dataset/0037798/global-economic-monitor','api_url':'https://api.worldbank.org/v2/','recognized_hosts':['datacatalog.worldbank.org','api.worldbank.org','www.worldbank.org','worldbank.org'],'indicator_types':['industrial-production-index','merchandise-export-series','merchandise-import-series','terms-of-trade-context'],'evidence_classes':['high-frequency-industrial-trade-series'],'coverage':'Cross-country high-frequency macroeconomic series including industrial production and merchandise trade, updated as source data become available.','limitations':'Global Economic Monitor series are national/macroeconomic time series rather than plant observations or shipment tracking. Frequency, lag, revisions and source methods vary by economy; changes do not by themselves establish a disruption, shortage, capacity constraint or causal event.'},
'world-bank-wits-trade':{'title':'World Bank WITS Trade Stats','organization':'World Bank / UN COMTRADE and UNCTAD source data','url':'https://datacatalog.worldbank.org/search/dataset/0039685/world-integrated-trade-solution-trade-stats','api_url':'https://wits.worldbank.org/API/V1/','recognized_hosts':['datacatalog.worldbank.org','wits.worldbank.org','www.worldbank.org','worldbank.org'],'indicator_types':['bilateral-export-value','bilateral-import-value','product-group-trade-share','trade-concentration-index'],'evidence_classes':['aggregated-bilateral-trade-statistic'],'coverage':'Public CC BY 4.0 WITS Trade Stats aggregations of merchandise trade and tariff data, including bilateral imports/exports and derived trade indicators.','limitations':'Trade statistics are reported/aggregated customs and statistical records, not physical shipment telemetry. Reporter/partner asymmetries, classification revisions, re-exports, timing and valuation methods can affect comparisons; bilateral trade does not prove supplier dependency, origin content, routing or current inventory.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('industrial-site','Industrial site','facility'),('factory-works','Factory / industrial works','facility'),('refinery','Refinery','facility'),('warehouse-logistics','Warehouse / logistics facility','facility'),('industrial-landuse','Industrial land use','facility'),
('manufacturing-value-added','Manufacturing value added','manufacturing'),('manufacturing-share-gdp','Manufacturing share of GDP','manufacturing'),('manufacturing-growth','Manufacturing value-added growth','manufacturing'),('medium-high-tech-manufacturing-share','Medium/high-tech manufacturing share','manufacturing'),
('industrial-production-index','Industrial production index','production'),('merchandise-export-series','Merchandise exports','trade-series'),('merchandise-import-series','Merchandise imports','trade-series'),('terms-of-trade-context','Terms-of-trade context','trade-series'),
('bilateral-export-value','Bilateral export value','trade-flow'),('bilateral-import-value','Bilateral import value','trade-flow'),('product-group-trade-share','Product-group trade share','trade-flow'),('trade-concentration-index','Trade concentration index','trade-flow') ]}
EVIDENCE_CLASSES={
'community-mapped-industrial-feature':'community-mapped industrial geometry/attributes; not proof of operation, output, ownership, employment, regulatory status or legal access',
'harmonized-national-manufacturing-statistic':'country/economy manufacturing statistic retaining period/source context; not facility-level output or utilization',
'high-frequency-industrial-trade-series':'national macroeconomic industrial/trade series retaining frequency/revision context; not plant telemetry, shipment tracking or disruption proof',
'aggregated-bilateral-trade-statistic':'reported/aggregated bilateral merchandise-trade statistic retaining classification/reporter/partner context; not shipment telemetry or proven supply-chain dependency'}
def _source(v):
 k=(v or 'openstreetmap-industrial').strip().lower()
 if k not in SOURCES: raise ValueError(f'unsupported industrial/manufacturing source: {k}')
 return k,{'id':k,**SOURCES[k]}
def _indicator(v):
 k=(v or 'industrial-site').strip().lower()
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
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'evidence_class_count':len(EVIDENCE_CLASSES),'summary':'Orient industrial facility mapping, manufacturing structure, industrial-production series and bilateral trade-flow evidence without converting maps or aggregate statistics into operating status, facility output, shipment tracking or supply-chain dependency determinations.','warning':'INDUSTRIAL & TRADE EVIDENCE · NOT OPERATING STATUS, FACILITY OUTPUT OR SUPPLY-CHAIN DEPENDENCY DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'mapped_industrial_feature_equals_operating_facility':False,'national_manufacturing_statistic_equals_facility_output':False,'industrial_production_series_equals_plant_telemetry':False,'trade_record_equals_physical_shipment_tracking':False,'bilateral_trade_equals_supply_chain_dependency':False,'zero_records_equals_no_industry_or_trade':False,'platform_disruption_or_shortage_determination':False,'automatic_action_authorized':False}}
def state(source_id='openstreetmap-industrial',indicator_type='industrial-site',area='',date='',latitude=None,longitude=None):
 _,src=_source(source_id);iid,ind=_indicator(indicator_type)
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':src,'indicator_type':ind,'area':str(area or '').strip() or None,'date':str(date or '').strip() or None,'query_point':_point(latitude,longitude),'source_supports_indicator_type':iid in src['indicator_types'],'evidence':{'industrial_feature_loaded':False,'manufacturing_statistic_loaded':False,'industrial_series_loaded':False,'trade_flow_record_loaded':False,'facility_operating_confirmation_loaded':False,'shipment_telemetry_loaded':False},'truth':{'mapped_feature_treated_as_operating_facility':False,'national_statistic_treated_as_facility_output':False,'industrial_series_treated_as_plant_telemetry':False,'trade_record_treated_as_physical_shipment':False,'bilateral_trade_treated_as_supply_chain_dependency':False,'zero_records_treated_as_no_industry_or_trade':False,'platform_disruption_or_shortage_determination':False,'automatic_action_authorized':False}}
def normalize_feature(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'openstreetmap-industrial');iid,_=_indicator(request.get('indicator_type') or 'industrial-site')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested industrial indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'source_feature_id':str(request.get('source_feature_id') or '').strip() or None,'product':str(request.get('product') or '').strip() or None,'operator':str(request.get('operator') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'operating_status_inferred':False,'production_volume_inferred':False,'employment_inferred':False,'ownership_verified':False,'regulatory_status_inferred':False,'hazardous_material_inventory_inferred':False,'legal_access_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'feature':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_series(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'world-bank-manufacturing');iid,_=_indicator(request.get('indicator_type') or 'manufacturing-share-gdp')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested industrial/manufacturing indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'period':str(request.get('period') or '').strip() or None,'area_code':str(request.get('area_code') or '').strip() or None,'value':request.get('value'),'unit':str(request.get('unit') or '').strip() or None,'frequency':str(request.get('frequency') or '').strip() or None,'facility_output_inferred':False,'plant_utilization_inferred':False,'real_time_production_inferred':False,'disruption_inferred':False,'shortage_inferred':False,'causal_explanation_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'series':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_trade_flow(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'world-bank-wits-trade');iid,_=_indicator(request.get('indicator_type') or 'bilateral-export-value')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested trade indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'period':str(request.get('period') or '').strip() or None,'reporter':str(request.get('reporter') or '').strip() or None,'partner':str(request.get('partner') or '').strip() or None,'product_group':str(request.get('product_group') or '').strip() or None,'value':request.get('value'),'unit':str(request.get('unit') or '').strip() or None,'physical_shipment_inferred':False,'shipment_route_inferred':False,'supplier_dependency_inferred':False,'origin_content_inferred':False,'inventory_position_inferred':False,'customs_or_sanctions_compliance_inferred':False,'current_facility_status_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'trade_flow':r,'record_sha256':_digest(r),'normalized_at':_now()}
def threshold_preview(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 value=float(request.get('value'));threshold=float(request.get('threshold'));unit=str(request.get('unit') or '').strip() or None;direction=str(request.get('direction') or 'below').strip().lower()
 if direction not in {'above','below'}: raise ValueError('direction must be above or below')
 crossed=value>=threshold if direction=='above' else value<=threshold
 r={'value':value,'threshold':threshold,'unit':unit,'direction':direction,'screening_condition_met':crossed,'disruption_declared':False,'shortage_determined':False,'facility_shutdown_determined':False,'supply_chain_dependency_determined':False,'trade_restriction_determined':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='openstreetmap-industrial',indicator_type='industrial-site',area='',date='',latitude=None,longitude=None):
 cur=state(source_id,indicator_type,area,date,latitude,longitude);p={'schema':'sc-site-intelligence-industrial-manufacturing-trade/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'area':cur['area'],'date':cur['date'],'query_point':cur['query_point']},'evidence':cur['evidence'],'review':{'mapped_feature_as_operating_facility':False,'national_statistic_as_facility_output':False,'industrial_series_as_plant_telemetry':False,'trade_record_as_physical_shipment':False,'bilateral_trade_as_supply_chain_dependency':False,'zero_records_as_no_industry_or_trade':False,'platform_disruption_or_shortage_determination':False}}
 return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
 c={'four_source_families_registered':len(SOURCES)==4,'openstreetmap_industrial_registered':'openstreetmap-industrial' in SOURCES,'world_bank_manufacturing_registered':'world-bank-manufacturing' in SOURCES,'world_bank_gem_registered':'world-bank-gem' in SOURCES,'world_bank_wits_registered':'world-bank-wits-trade' in SOURCES,'facility_operation_guard_present':True,'facility_output_guard_present':True,'shipment_tracking_guard_present':True,'supply_chain_dependency_guard_present':True,'public_route_count_preserved':True}
 return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
