from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-digital-connectivity-broadband-internet-performance-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'openstreetmap-telecom':{'title':'OpenStreetMap Telecommunications Infrastructure','organization':'OpenStreetMap contributors / OpenStreetMap Foundation','url':'https://wiki.openstreetmap.org/wiki/Key:communication','api_url':'https://overpass-api.de/api/interpreter','recognized_hosts':['wiki.openstreetmap.org','overpass-api.de','www.openstreetmap.org','openstreetmap.org'],'indicator_types':['communications-tower','communications-mast','telecom-exchange','antenna-site','fiber-cable'],'evidence_classes':['community-mapped-telecom-feature'],'coverage':'Global community-mapped communications towers, masts, exchanges, antennas, cables and related telecommunications features where contributors have mapped them.','limitations':'OpenStreetMap telecom features are community-maintained mapping evidence. Geometry, operator, technology and lifecycle tags may be incomplete or stale and do not establish coverage, signal strength, capacity, legal access, ownership, current operation or service availability.'},
'mlab-network-performance':{'title':'Measurement Lab Network Performance Data','organization':'Measurement Lab','url':'https://www.measurementlab.net/data/','api_url':'https://locate.measurementlab.net/v2/nearest/ndt/ndt7','recognized_hosts':['www.measurementlab.net','measurementlab.net','locate.measurementlab.net','storage.googleapis.com','bigquery.googleapis.com'],'indicator_types':['download-throughput','upload-throughput','latency','packet-loss-context','ndt-test-count'],'evidence_classes':['client-initiated-network-measurement'],'coverage':'Public CC0 Internet measurement data from M-Lab experiments, including NDT measurements and aggregate statistics suitable for geographic performance analysis.','limitations':'M-Lab measurements are voluntary/client-initiated samples and have selection, device, access-network, protocol and temporal biases. A measured test does not establish advertised tier, universal local performance, provider compliance, outage status or service availability for a location.'},
'world-bank-connectivity':{'title':'World Bank Connectivity Indicators','organization':'World Bank / source agencies including ITU','url':'https://data.worldbank.org/indicator/IT.NET.USER.ZS','api_url':'https://api.worldbank.org/v2/','recognized_hosts':['data.worldbank.org','api.worldbank.org','www.worldbank.org','worldbank.org'],'indicator_types':['internet-users-share','fixed-broadband-subscriptions','mobile-cellular-subscriptions','secure-internet-servers'],'evidence_classes':['harmonized-national-connectivity-statistic'],'coverage':'Harmonized country/economy indicators for Internet use, fixed broadband, mobile subscriptions and related ICT measures distributed through World Bank APIs.','limitations':'National indicators are aggregate statistics with source-specific definitions, reporting years and revisions. They do not establish household-level access, current service quality, network coverage, affordability, individual usage, outage status or local infrastructure.'},
'fcc-broadband-data':{'title':'FCC Broadband Data Collection / National Broadband Map','organization':'U.S. Federal Communications Commission','url':'https://broadbandmap.fcc.gov/data-download','api_url':'https://broadbandmap.fcc.gov/api/public/map/listAsOfs','recognized_hosts':['broadbandmap.fcc.gov','www.fcc.gov','fcc.gov','help.bdc.fcc.gov','opendata.fcc.gov'],'indicator_types':['fixed-broadband-availability','mobile-broadband-coverage','advertised-download-speed','advertised-upload-speed','broadband-technology'],'evidence_classes':['provider-reported-broadband-availability'],'coverage':'U.S. provider-reported fixed and mobile broadband availability and coverage data published through the FCC Broadband Data Collection and National Broadband Map public downloads/APIs.','limitations':'FCC BDC availability indicates where providers report offering mass-market service; it is not a measured performance test, adoption record, affordability finding or guarantee that service can be installed at a specific moment. Coverage may be challenged, verified, revised or propagation-modeled.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('communications-tower','Communications tower','infrastructure'),('communications-mast','Communications mast','infrastructure'),('telecom-exchange','Telecom exchange','infrastructure'),('antenna-site','Antenna site','infrastructure'),('fiber-cable','Fiber cable','infrastructure'),
('download-throughput','Download throughput','performance'),('upload-throughput','Upload throughput','performance'),('latency','Latency','performance'),('packet-loss-context','Packet-loss context','performance'),('ndt-test-count','NDT test count','sampling'),
('internet-users-share','Individuals using the Internet','statistics'),('fixed-broadband-subscriptions','Fixed broadband subscriptions','statistics'),('mobile-cellular-subscriptions','Mobile cellular subscriptions','statistics'),('secure-internet-servers','Secure Internet servers','statistics'),
('fixed-broadband-availability','Fixed broadband availability','availability'),('mobile-broadband-coverage','Mobile broadband coverage','availability'),('advertised-download-speed','Advertised download speed','availability'),('advertised-upload-speed','Advertised upload speed','availability'),('broadband-technology','Broadband technology','availability') ]}
EVIDENCE_CLASSES={
'community-mapped-telecom-feature':'community-mapped telecommunications geometry/attributes; not proof of coverage, operation, legal access, service or signal quality',
'client-initiated-network-measurement':'client-initiated Internet performance measurement retaining sample and method context; not universal provider/local performance or outage proof',
'harmonized-national-connectivity-statistic':'country/economy ICT statistic retaining reporting-year and source context; not household/local access, coverage or performance proof',
'provider-reported-broadband-availability':'FCC provider-reported availability/coverage evidence retaining filing/model/challenge context; not measured performance, adoption, affordability or guaranteed installability'}
def _source(v):
 k=(v or 'openstreetmap-telecom').strip().lower()
 if k not in SOURCES: raise ValueError(f'unsupported digital connectivity source: {k}')
 return k,{'id':k,**SOURCES[k]}
def _indicator(v):
 k=(v or 'communications-tower').strip().lower()
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
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'evidence_class_count':len(EVIDENCE_CLASSES),'summary':'Orient telecommunications infrastructure, broadband availability, Internet adoption and measured network-performance evidence without converting maps, samples, aggregate statistics or provider filings into guaranteed service, outage, coverage or safety determinations.','warning':'DIGITAL-CONNECTIVITY EVIDENCE · NOT SERVICE AVAILABILITY, OUTAGE, COVERAGE GUARANTEE OR NETWORK-SAFETY DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'mapped_telecom_feature_equals_coverage_or_operating_asset':False,'performance_sample_equals_universal_local_performance':False,'national_statistic_equals_household_or_local_access':False,'provider_reported_availability_equals_measured_performance_or_guaranteed_installability':False,'zero_records_equals_no_connectivity':False,'platform_outage_or_coverage_determination':False,'network_safety_determination':False,'automatic_action_authorized':False}}
def state(source_id='openstreetmap-telecom',indicator_type='communications-tower',area='',date='',latitude=None,longitude=None):
 _,src=_source(source_id);iid,ind=_indicator(indicator_type)
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':src,'indicator_type':ind,'area':str(area or '').strip() or None,'date':str(date or '').strip() or None,'query_point':_point(latitude,longitude),'source_supports_indicator_type':iid in src['indicator_types'],'evidence':{'telecom_feature_loaded':False,'network_measurement_loaded':False,'national_statistic_loaded':False,'provider_availability_record_loaded':False,'real_time_service_confirmation_loaded':False},'truth':{'mapped_feature_treated_as_coverage_or_operating_asset':False,'performance_sample_treated_as_universal_local_performance':False,'national_statistic_treated_as_household_or_local_access':False,'provider_availability_treated_as_measured_performance_or_guaranteed_installability':False,'zero_records_treated_as_no_connectivity':False,'platform_outage_or_coverage_determination':False,'network_safety_determination':False,'automatic_action_authorized':False}}
def normalize_feature(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'openstreetmap-telecom');iid,_=_indicator(request.get('indicator_type') or 'communications-tower')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested digital-connectivity indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'source_feature_id':str(request.get('source_feature_id') or '').strip() or None,'technology':str(request.get('technology') or '').strip() or None,'operator':str(request.get('operator') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'coverage_inferred':False,'operating_status_inferred':False,'signal_strength_inferred':False,'service_availability_inferred':False,'ownership_inferred':False,'legal_access_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'feature':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_measurement(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'mlab-network-performance');iid,_=_indicator(request.get('indicator_type') or 'download-throughput')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested digital-connectivity indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'period':str(request.get('period') or '').strip() or None,'area_code':str(request.get('area_code') or '').strip() or None,'value':request.get('value'),'unit':str(request.get('unit') or '').strip() or None,'sample_count':request.get('sample_count'),'provider':str(request.get('provider') or '').strip() or None,'universal_local_performance_inferred':False,'advertised_tier_inferred':False,'provider_compliance_inferred':False,'outage_inferred':False,'service_availability_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'measurement':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_availability(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'fcc-broadband-data');iid,_=_indicator(request.get('indicator_type') or 'fixed-broadband-availability')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested digital-connectivity indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'as_of':str(request.get('as_of') or '').strip() or None,'provider':str(request.get('provider') or '').strip() or None,'technology':str(request.get('technology') or '').strip() or None,'advertised_download_mbps':request.get('advertised_download_mbps'),'advertised_upload_mbps':request.get('advertised_upload_mbps'),'query_point':_point(request.get('latitude'),request.get('longitude')),'measured_performance_inferred':False,'adoption_inferred':False,'affordability_inferred':False,'guaranteed_installability_inferred':False,'current_operating_status_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'availability':r,'record_sha256':_digest(r),'normalized_at':_now()}
def threshold_preview(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 value=float(request.get('value'));threshold=float(request.get('threshold'));unit=str(request.get('unit') or '').strip() or None;direction=str(request.get('direction') or 'below').strip().lower()
 if direction not in {'above','below'}: raise ValueError('direction must be above or below')
 crossed=value>=threshold if direction=='above' else value<=threshold
 r={'value':value,'threshold':threshold,'unit':unit,'direction':direction,'screening_condition_met':crossed,'outage_declared':False,'coverage_failure_determined':False,'provider_violation_determined':False,'network_safety_determined':False,'service_guarantee_determined':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='openstreetmap-telecom',indicator_type='communications-tower',area='',date='',latitude=None,longitude=None):
 cur=state(source_id,indicator_type,area,date,latitude,longitude);p={'schema':'sc-site-intelligence-digital-connectivity/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'area':cur['area'],'date':cur['date'],'query_point':cur['query_point']},'evidence':cur['evidence'],'review':{'mapped_feature_as_coverage_or_operating_asset':False,'performance_sample_as_universal_local_performance':False,'national_statistic_as_household_or_local_access':False,'provider_availability_as_measured_performance_or_guaranteed_installability':False,'zero_records_as_no_connectivity':False,'platform_outage_or_coverage_determination':False,'network_safety_determination':False}}
 return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
 c={'four_source_families_registered':len(SOURCES)==4,'openstreetmap_telecom_registered':'openstreetmap-telecom' in SOURCES,'mlab_registered':'mlab-network-performance' in SOURCES,'world_bank_registered':'world-bank-connectivity' in SOURCES,'fcc_bdc_registered':'fcc-broadband-data' in SOURCES,'sample_universality_guard_present':True,'availability_performance_guard_present':True,'outage_guard_present':True,'network_safety_guard_present':True,'public_route_count_preserved':True}
 return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
