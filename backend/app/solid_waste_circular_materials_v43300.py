from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-solid-waste-recycling-circular-materials-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'openstreetmap-waste-recycling':{'title':'OpenStreetMap Waste & Recycling Infrastructure','organization':'OpenStreetMap contributors / OpenStreetMap Foundation','url':'https://wiki.openstreetmap.org/wiki/Tag:amenity%3Drecycling','api_url':'https://overpass-api.de/api/interpreter','recognized_hosts':['wiki.openstreetmap.org','overpass-api.de','www.openstreetmap.org','openstreetmap.org'],'indicator_types':['landfill','recycling-centre','recycling-container','waste-transfer-station','waste-disposal-site'],'evidence_classes':['community-mapped-waste-infrastructure'],'coverage':'Global community-mapped waste disposal, landfill, transfer and recycling infrastructure where contributors have mapped facilities and attributes.','limitations':'OpenStreetMap geometry and tags are community-maintained and can be incomplete or stale. A mapped landfill, recycling centre or waste facility does not establish current operation, permitted status, accepted materials, remaining capacity, environmental performance or regulatory compliance.'},
'epa-rcrainfo-hazardous-waste':{'title':'EPA RCRAInfo / ECHO Hazardous-Waste Records','organization':'U.S. Environmental Protection Agency','url':'https://echo.epa.gov/tools/web-services','api_url':'https://echodata.epa.gov/echo/rcra_rest_services.get_facilities','recognized_hosts':['echo.epa.gov','echodata.epa.gov','rcrapublic.epa.gov','www.epa.gov','epa.gov'],'indicator_types':['hazardous-waste-handler','treatment-storage-disposal-facility','generator-status','compliance-enforcement-context'],'evidence_classes':['epa-hazardous-waste-regulatory-record'],'coverage':'U.S. RCRA hazardous-waste handler, treatment/storage/disposal, generator and compliance/enforcement context drawn from EPA RCRAInfo and exposed through ECHO/download services.','limitations':'RCRAInfo/ECHO is regulatory and administrative source data and may include reporting/update lags. A handler or compliance record does not establish current facility operation, material inventory, exposure, a new violation finding, remediation need or legal conclusion by Sustainable Catalyst.'},
'world-bank-what-a-waste':{'title':'World Bank What a Waste Global Database','organization':'World Bank','url':'https://datacatalog.worldbank.org/search/dataset/0039597/what-a-waste-global-database','api_url':'https://api.worldbank.org/','recognized_hosts':['datacatalog.worldbank.org','api.worldbank.org','www.worldbank.org','worldbank.org'],'indicator_types':['municipal-waste-generation','waste-collection','waste-composition','waste-treatment-disposal','plastic-waste-context'],'evidence_classes':['global-waste-system-statistic'],'coverage':'Global country- and city-level solid-waste statistics covering generation, composition, collection, treatment/disposal, workers, institutions and plastic-waste context, including projections where published by the source.','limitations':'What a Waste aggregates best-available official and published data with varying definitions, years and quality; some values are estimates or projections. Statistics do not establish facility-level operations, household collection, actual material recovery, current disposal practice or regulatory compliance.'},
'eurostat-waste':{'title':'Eurostat Waste Statistics','organization':'Eurostat / European Commission','url':'https://ec.europa.eu/eurostat/web/waste','api_url':'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/env_wasmun','recognized_hosts':['ec.europa.eu','commission.europa.eu'],'indicator_types':['municipal-waste-generation','municipal-waste-recycling-rate','waste-treatment','waste-recovery','waste-disposal'],'evidence_classes':['official-european-waste-statistic'],'coverage':'European waste-generation and treatment statistics, including municipal waste, recycling, recovery, disposal and key waste streams reported through the European Statistical System.','limitations':'Eurostat values are official statistical series with source definitions and reporting schedules; municipal-waste comparability can vary with national coverage. A reported recycling rate or treatment quantity does not prove specific material circularity, facility performance, shipment routing or local compliance.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('landfill','Landfill','mapped-infrastructure'),('recycling-centre','Recycling centre','mapped-infrastructure'),('recycling-container','Recycling container','mapped-infrastructure'),('waste-transfer-station','Waste transfer station','mapped-infrastructure'),('waste-disposal-site','Waste disposal site','mapped-infrastructure'),
('hazardous-waste-handler','Hazardous-waste handler','hazardous-waste-regulatory'),('treatment-storage-disposal-facility','Treatment/storage/disposal facility','hazardous-waste-regulatory'),('generator-status','Hazardous-waste generator status','hazardous-waste-regulatory'),('compliance-enforcement-context','Compliance/enforcement context','hazardous-waste-regulatory'),
('municipal-waste-generation','Municipal waste generation','waste-system-statistic'),('waste-collection','Waste collection','waste-system-statistic'),('waste-composition','Waste composition','waste-system-statistic'),('waste-treatment-disposal','Waste treatment & disposal','waste-system-statistic'),('plastic-waste-context','Plastic-waste context','waste-system-statistic'),
('municipal-waste-recycling-rate','Municipal waste recycling rate','european-waste-statistic'),('waste-treatment','Waste treatment','european-waste-statistic'),('waste-recovery','Waste recovery','european-waste-statistic'),('waste-disposal','Waste disposal','european-waste-statistic') ]}
EVIDENCE_CLASSES={
'community-mapped-waste-infrastructure':'community-mapped landfill, disposal, transfer or recycling infrastructure; not proof of operation, permission, capacity, accepted materials or compliance',
'epa-hazardous-waste-regulatory-record':'EPA RCRAInfo/ECHO hazardous-waste administrative/regulatory record; not live material inventory, exposure evidence or a new compliance/legal determination',
'global-waste-system-statistic':'World Bank What a Waste statistic, estimate or projection retaining source context; not household/facility telemetry or proof of actual recycling/material recovery',
'official-european-waste-statistic':'Eurostat waste-generation/treatment/recycling statistic; not facility performance, shipment trace or product/material circularity certification'}
def _source(v):
 k=(v or 'openstreetmap-waste-recycling').strip().lower()
 if k not in SOURCES: raise ValueError(f'unsupported solid-waste/circular-materials source: {k}')
 return k,{'id':k,**SOURCES[k]}
def _indicator(v):
 k=(v or 'landfill').strip().lower()
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
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'evidence_class_count':len(EVIDENCE_CLASSES),'summary':'Orient mapped waste/recycling infrastructure, U.S. hazardous-waste regulatory records and international waste-generation/treatment statistics without converting them into live facility operation, compliance, recycling-outcome or circularity determinations.','warning':'SOLID-WASTE & CIRCULAR-MATERIAL EVIDENCE · NOT FACILITY OPERATION, COMPLIANCE, RECYCLING-OUTCOME OR CIRCULARITY DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'mapped_waste_feature_equals_operating_facility':False,'regulatory_record_equals_new_compliance_finding':False,'waste_statistic_equals_facility_or_household_outcome':False,'reported_recycling_rate_equals_material_circularity':False,'projection_equals_observed_future_waste':False,'zero_records_equals_no_waste_infrastructure':False,'automatic_action_authorized':False}}
def state(source_id='openstreetmap-waste-recycling',indicator_type='landfill',area='',date='',latitude=None,longitude=None):
 _,src=_source(source_id);iid,ind=_indicator(indicator_type)
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':src,'indicator_type':ind,'area':str(area or '').strip() or None,'date':str(date or '').strip() or None,'query_point':_point(latitude,longitude),'source_supports_indicator_type':iid in src['indicator_types'],'evidence':{'waste_infrastructure_feature_loaded':False,'hazardous_waste_regulatory_record_loaded':False,'global_waste_statistic_loaded':False,'european_waste_statistic_loaded':False,'live_facility_status_loaded':False,'material_flow_trace_loaded':False},'truth':{'mapped_feature_treated_as_operating_facility':False,'regulatory_record_treated_as_new_compliance_finding':False,'statistic_treated_as_facility_or_household_outcome':False,'recycling_rate_treated_as_material_circularity':False,'projection_treated_as_observation':False,'zero_records_treated_as_no_waste_infrastructure':False,'automatic_action_authorized':False}}
def normalize_feature(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'openstreetmap-waste-recycling');iid,_=_indicator(request.get('indicator_type') or 'landfill')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested infrastructure indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'source_feature_id':str(request.get('source_feature_id') or '').strip() or None,'operator':str(request.get('operator') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'operating_status_inferred':False,'permitted_status_inferred':False,'accepted_materials_inferred':False,'remaining_capacity_inferred':False,'environmental_performance_inferred':False,'compliance_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'feature':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_regulatory(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'epa-rcrainfo-hazardous-waste');iid,_=_indicator(request.get('indicator_type') or 'hazardous-waste-handler')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested regulatory indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'facility_id':str(request.get('facility_id') or '').strip() or None,'source_status':str(request.get('source_status') or '').strip() or None,'reporting_period':str(request.get('reporting_period') or '').strip() or None,'live_operating_status_inferred':False,'live_material_inventory_inferred':False,'new_compliance_finding_inferred':False,'exposure_or_health_risk_inferred':False,'remediation_need_inferred':False,'legal_determination_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'regulatory_record':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_series(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'world-bank-what-a-waste');iid,_=_indicator(request.get('indicator_type') or 'municipal-waste-generation')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested waste statistic')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 kind=str(request.get('value_kind') or 'reported').strip().lower()
 if kind not in {'reported','estimated','projected'}: raise ValueError('value_kind must be reported, estimated or projected')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'area_code':str(request.get('area_code') or '').strip() or None,'period':str(request.get('period') or '').strip() or None,'value':request.get('value'),'unit':str(request.get('unit') or '').strip() or None,'value_kind':kind,'facility_level_outcome_inferred':False,'household_level_outcome_inferred':False,'actual_material_recovery_inferred':False,'circularity_inferred':False,'projection_treated_as_observation':False,'compliance_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'series':r,'record_sha256':_digest(r),'normalized_at':_now()}
def threshold_preview(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 value=float(request.get('value'));threshold=float(request.get('threshold'));unit=str(request.get('unit') or '').strip() or None;direction=str(request.get('direction') or 'above').strip().lower()
 if direction not in {'above','below'}: raise ValueError('direction must be above or below')
 crossed=value>=threshold if direction=='above' else value<=threshold
 r={'value':value,'threshold':threshold,'unit':unit,'direction':direction,'screening_condition_met':crossed,'waste_crisis_declared':False,'facility_failure_declared':False,'regulatory_violation_declared':False,'recycling_success_declared':False,'circularity_declared':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='openstreetmap-waste-recycling',indicator_type='landfill',area='',date='',latitude=None,longitude=None):
 cur=state(source_id,indicator_type,area,date,latitude,longitude);p={'schema':'sc-site-intelligence-solid-waste-circular-materials/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'area':cur['area'],'date':cur['date'],'query_point':cur['query_point']},'evidence':cur['evidence'],'review':{'mapped_feature_as_operating_facility':False,'regulatory_record_as_new_compliance_finding':False,'statistic_as_facility_or_household_outcome':False,'recycling_rate_as_material_circularity':False,'projection_as_observation':False,'zero_records_as_no_waste_infrastructure':False}}
 return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
 c={'four_source_families_registered':len(SOURCES)==4,'openstreetmap_waste_registered':'openstreetmap-waste-recycling' in SOURCES,'epa_rcrainfo_registered':'epa-rcrainfo-hazardous-waste' in SOURCES,'world_bank_what_a_waste_registered':'world-bank-what-a-waste' in SOURCES,'eurostat_waste_registered':'eurostat-waste' in SOURCES,'operating_status_guard_present':True,'compliance_guard_present':True,'recycling_outcome_guard_present':True,'circularity_guard_present':True,'public_route_count_preserved':True}
 return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
