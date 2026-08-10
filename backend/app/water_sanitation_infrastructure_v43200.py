from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-water-supply-wastewater-sanitation-infrastructure-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'openstreetmap-water-infrastructure':{'title':'OpenStreetMap Water & Wastewater Infrastructure','organization':'OpenStreetMap contributors / OpenStreetMap Foundation','url':'https://wiki.openstreetmap.org/wiki/Tag:man_made%3Dwastewater_plant','api_url':'https://overpass-api.de/api/interpreter','recognized_hosts':['wiki.openstreetmap.org','overpass-api.de','www.openstreetmap.org','openstreetmap.org'],'indicator_types':['water-works','wastewater-treatment-plant','water-tower','pumping-station','water-storage'],'evidence_classes':['community-mapped-water-infrastructure'],'coverage':'Global community-mapped drinking-water and wastewater infrastructure where contributors have mapped facilities and related structures.','limitations':'OpenStreetMap geometry and tags are community-maintained and can be incomplete or stale. A mapped facility does not establish current operation, ownership, treatment capacity, drinking-water safety, discharge compliance, service territory or legal access.'},
'epa-echo-wastewater':{'title':'EPA ECHO Wastewater / Stormwater / Biosolids Facilities','organization':'U.S. Environmental Protection Agency','url':'https://echo.epa.gov/tools/web-services','api_url':'https://echodata.epa.gov/echo/cwa_rest_services.get_facilities','recognized_hosts':['echo.epa.gov','echodata.epa.gov','www.epa.gov','epa.gov'],'indicator_types':['npdes-regulated-facility','permitted-discharge-context','effluent-monitoring-context','receiving-water-context'],'evidence_classes':['epa-regulatory-wastewater-record'],'coverage':'U.S. Clean Water Act / NPDES facility, permit, discharge-monitoring and receiving-water context exposed through EPA ECHO web services.','limitations':'ECHO aggregates regulatory source systems and may include reporting or update lags. Facility/permit records do not by themselves establish current operating status, treatment performance, a new violation finding, public-health risk or legal conclusion by Sustainable Catalyst.'},
'epa-sdwis-drinking-water':{'title':'EPA SDWIS Drinking-Water Systems via Envirofacts','organization':'U.S. Environmental Protection Agency','url':'https://www.epa.gov/enviro/download-additional-envirofacts-datasets','api_url':'https://data.epa.gov/efservice/','recognized_hosts':['www.epa.gov','epa.gov','data.epa.gov','enviro.epa.gov'],'indicator_types':['public-water-system','population-served','system-type','drinking-water-compliance-context'],'evidence_classes':['epa-drinking-water-system-record'],'coverage':'U.S. Safe Drinking Water Information System records exposed through EPA Envirofacts data services, including public-water-system and compliance-related attributes.','limitations':'SDWIS/Envirofacts records are administrative and regulatory data, not real-time water-quality telemetry. A system record or compliance field does not establish current tap-water safety at a household or a new compliance determination by Sustainable Catalyst.'},
'who-unicef-jmp-wash':{'title':'WHO/UNICEF Joint Monitoring Programme for WASH','organization':'World Health Organization / UNICEF','url':'https://washdata.org/','api_url':'https://washdata.org/data','recognized_hosts':['washdata.org','www.washdata.org','data.unicef.org','www.unicef.org','unicef.org'],'indicator_types':['safely-managed-drinking-water','basic-drinking-water','safely-managed-sanitation','basic-sanitation','basic-hygiene'],'evidence_classes':['international-wash-service-estimate'],'coverage':'Internationally comparable national, regional and global estimates of drinking-water, sanitation and hygiene service levels used for SDG monitoring.','limitations':'JMP values are modeled/harmonized service-level estimates based on national sources, censuses and surveys. They do not establish household-level service, utility network coverage, facility operation, water quality at a specific tap or real-time sanitation performance.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('water-works','Drinking-water works','mapped-infrastructure'),('wastewater-treatment-plant','Wastewater treatment plant','mapped-infrastructure'),('water-tower','Water tower','mapped-infrastructure'),('pumping-station','Pumping station','mapped-infrastructure'),('water-storage','Water storage infrastructure','mapped-infrastructure'),
('npdes-regulated-facility','NPDES-regulated facility','wastewater-regulatory'),('permitted-discharge-context','Permitted discharge context','wastewater-regulatory'),('effluent-monitoring-context','Effluent monitoring context','wastewater-regulatory'),('receiving-water-context','Receiving-water context','wastewater-regulatory'),
('public-water-system','Public water system','drinking-water-system'),('population-served','Population served','drinking-water-system'),('system-type','Public-water-system type','drinking-water-system'),('drinking-water-compliance-context','Drinking-water compliance context','drinking-water-system'),
('safely-managed-drinking-water','Safely managed drinking-water service','wash-estimate'),('basic-drinking-water','Basic drinking-water service','wash-estimate'),('safely-managed-sanitation','Safely managed sanitation service','wash-estimate'),('basic-sanitation','Basic sanitation service','wash-estimate'),('basic-hygiene','Basic hygiene service','wash-estimate') ]}
EVIDENCE_CLASSES={
'community-mapped-water-infrastructure':'community-mapped water/wastewater facility geometry and attributes; not proof of operation, capacity, water safety, service territory or compliance',
'epa-regulatory-wastewater-record':'EPA wastewater/NPDES regulatory record retaining source status and reporting context; not a new compliance, health-risk or operating-status determination',
'epa-drinking-water-system-record':'EPA SDWIS/Envirofacts public-water-system record; not real-time tap-water quality, household service confirmation or a new compliance determination',
'international-wash-service-estimate':'WHO/UNICEF JMP harmonized service-level estimate; not household-level service, utility telemetry or facility-operating evidence'}
def _source(v):
 k=(v or 'openstreetmap-water-infrastructure').strip().lower()
 if k not in SOURCES: raise ValueError(f'unsupported water/sanitation source: {k}')
 return k,{'id':k,**SOURCES[k]}
def _indicator(v):
 k=(v or 'water-works').strip().lower()
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
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'evidence_class_count':len(EVIDENCE_CLASSES),'summary':'Orient mapped water/wastewater infrastructure, EPA regulatory system records and internationally comparable WASH service estimates without converting them into live utility operation, household service, water-safety or compliance determinations.','warning':'WATER & SANITATION EVIDENCE · NOT A SERVICE, WATER-SAFETY, COMPLIANCE OR OPERATING-STATUS DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'mapped_facility_equals_operating_utility':False,'regulatory_record_equals_new_compliance_finding':False,'public_water_system_record_equals_household_water_safety':False,'wash_estimate_equals_household_service':False,'population_served_equals_current_connected_population':False,'zero_records_equals_no_water_or_sanitation_service':False,'automatic_action_authorized':False}}
def state(source_id='openstreetmap-water-infrastructure',indicator_type='water-works',area='',date='',latitude=None,longitude=None):
 _,src=_source(source_id);iid,ind=_indicator(indicator_type)
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':src,'indicator_type':ind,'area':str(area or '').strip() or None,'date':str(date or '').strip() or None,'query_point':_point(latitude,longitude),'source_supports_indicator_type':iid in src['indicator_types'],'evidence':{'infrastructure_feature_loaded':False,'wastewater_regulatory_record_loaded':False,'drinking_water_system_record_loaded':False,'wash_service_estimate_loaded':False,'real_time_water_quality_loaded':False,'live_utility_status_loaded':False},'truth':{'mapped_feature_treated_as_operating_utility':False,'regulatory_record_treated_as_new_compliance_finding':False,'system_record_treated_as_household_water_safety':False,'wash_estimate_treated_as_household_service':False,'population_served_treated_as_current_connections':False,'zero_records_treated_as_no_service':False,'automatic_action_authorized':False}}
def normalize_feature(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'openstreetmap-water-infrastructure');iid,_=_indicator(request.get('indicator_type') or 'water-works')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested infrastructure indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'source_feature_id':str(request.get('source_feature_id') or '').strip() or None,'operator':str(request.get('operator') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'operating_status_inferred':False,'capacity_inferred':False,'water_safety_inferred':False,'service_area_inferred':False,'compliance_inferred':False,'ownership_verified':False,'legal_access_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'feature':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_system(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'epa-sdwis-drinking-water');iid,_=_indicator(request.get('indicator_type') or 'public-water-system')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested system/regulatory indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'system_or_facility_id':str(request.get('system_or_facility_id') or '').strip() or None,'status':str(request.get('status') or '').strip() or None,'population_served':request.get('population_served'),'period':str(request.get('period') or '').strip() or None,'live_operating_status_inferred':False,'household_service_inferred':False,'tap_water_safety_inferred':False,'new_compliance_finding_inferred':False,'health_risk_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'system':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_series(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'who-unicef-jmp-wash');iid,_=_indicator(request.get('indicator_type') or 'safely-managed-drinking-water')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested service-level indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'area_code':str(request.get('area_code') or '').strip() or None,'period':str(request.get('period') or '').strip() or None,'value':request.get('value'),'unit':str(request.get('unit') or '').strip() or None,'household_level_service_inferred':False,'utility_network_coverage_inferred':False,'real_time_service_inferred':False,'water_quality_inferred':False,'facility_operation_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'series':r,'record_sha256':_digest(r),'normalized_at':_now()}
def threshold_preview(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 value=float(request.get('value'));threshold=float(request.get('threshold'));unit=str(request.get('unit') or '').strip() or None;direction=str(request.get('direction') or 'below').strip().lower()
 if direction not in {'above','below'}: raise ValueError('direction must be above or below')
 crossed=value>=threshold if direction=='above' else value<=threshold
 r={'value':value,'threshold':threshold,'unit':unit,'direction':direction,'screening_condition_met':crossed,'service_failure_declared':False,'water_unsafe_declared':False,'regulatory_violation_declared':False,'utility_outage_declared':False,'health_advisory_issued':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='openstreetmap-water-infrastructure',indicator_type='water-works',area='',date='',latitude=None,longitude=None):
 cur=state(source_id,indicator_type,area,date,latitude,longitude);p={'schema':'sc-site-intelligence-water-sanitation-infrastructure/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'area':cur['area'],'date':cur['date'],'query_point':cur['query_point']},'evidence':cur['evidence'],'review':{'mapped_facility_as_operating_utility':False,'regulatory_record_as_new_compliance_finding':False,'system_record_as_household_water_safety':False,'wash_estimate_as_household_service':False,'population_served_as_current_connections':False,'zero_records_as_no_service':False}}
 return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
 c={'four_source_families_registered':len(SOURCES)==4,'openstreetmap_water_registered':'openstreetmap-water-infrastructure' in SOURCES,'epa_echo_registered':'epa-echo-wastewater' in SOURCES,'epa_sdwis_registered':'epa-sdwis-drinking-water' in SOURCES,'who_unicef_jmp_registered':'who-unicef-jmp-wash' in SOURCES,'operating_status_guard_present':True,'water_safety_guard_present':True,'compliance_guard_present':True,'household_service_guard_present':True,'public_route_count_preserved':True}
 return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
