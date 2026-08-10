from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-transportation-networks-ports-airports-transit-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'overture-transportation':{'title':'Overture Maps Transportation','organization':'Overture Maps Foundation','url':'https://docs.overturemaps.org/guides/transportation/','api_url':'https://overturemapswestus2.blob.core.windows.net/release/','recognized_hosts':['docs.overturemaps.org','overturemapswestus2.blob.core.windows.net'],'indicator_types':['road-segment','rail-segment','water-transport-segment','network-connector'],'evidence_classes':['open-transport-network-feature'],'coverage':'Global open transportation segments and connectors covering road, rail and water networks, assembled from OpenStreetMap and additional provider/authoritative inputs.','limitations':'Transportation geometry and attributes are mapping evidence, not a guarantee that a segment is open, safe, legally accessible, suitable for a vehicle, current at the instant of use, or sufficient for turn-by-turn navigation.'},
'unece-unlocode':{'title':'UNECE UN/LOCODE','organization':'United Nations Economic Commission for Europe / UN/CEFACT','url':'https://unece.org/trade/uncefact/unlocode','api_url':'https://unlocode.unece.org/','recognized_hosts':['unece.org','unlocode.unece.org','service.unece.org'],'indicator_types':['trade-transport-location','port-location','rail-terminal-location','road-terminal-location','airport-location'],'evidence_classes':['unlocode-location-record'],'coverage':'Global coded locations used in international trade and transport, including function codes for ports, airports, rail terminals, road terminals and other logistics locations.','limitations':'UN/LOCODE identifies trade and transport locations. A listed code or function does not prove a facility is currently operating, available, unconstrained, owned by a particular entity, or suitable for a specific shipment or movement.'},
'ourairports':{'title':'OurAirports Open Airport Data','organization':'OurAirports open-data community','url':'https://ourairports.com/data/','api_url':'https://ourairports.com/data/','recognized_hosts':['ourairports.com','www.ourairports.com'],'indicator_types':['airport','runway','scheduled-service','navaid'],'evidence_classes':['community-airport-record'],'coverage':'Public-domain global airport, runway and navigation-aid records maintained as an open public-good dataset.','limitations':'OurAirports is community-maintained and not an official aeronautical information publication. Records must not be used as authoritative navigation, runway-operability, NOTAM, airspace, safety or regulatory evidence.'},
'mobilitydata-database':{'title':'Mobility Database','organization':'MobilityData','url':'https://mobilitydatabase.org/','api_url':'https://mobilitydata.github.io/mobility-feed-api/SwaggerUI/index.html','recognized_hosts':['mobilitydatabase.org','www.mobilitydatabase.org','mobilitydata.github.io'],'indicator_types':['gtfs-schedule-feed','gtfs-realtime-feed','gbfs-feed','transit-feed-coverage'],'evidence_classes':['mobility-feed-catalog-record'],'coverage':'Open global catalog of thousands of GTFS Schedule, GTFS Realtime and GBFS feeds, including feed metadata, coverage, quality reports and mirrored operator feeds.','limitations':'Catalog presence does not guarantee complete geographic coverage, current service, vehicle arrival, route operation, accessibility, fare availability or feed accuracy. Individual producer feeds retain their own licenses and conditions.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('road-segment','Road segment','network'),('rail-segment','Rail segment','network'),('water-transport-segment','Water transport segment','network'),('network-connector','Network connector','network'),
('trade-transport-location','Trade/transport location','logistics'),('port-location','Port location','logistics'),('rail-terminal-location','Rail terminal location','logistics'),('road-terminal-location','Road terminal location','logistics'),('airport-location','Airport location','logistics'),
('airport','Airport record','aviation'),('runway','Runway record','aviation'),('scheduled-service','Scheduled-service flag','aviation'),('navaid','Navigation-aid record','aviation'),
('gtfs-schedule-feed','GTFS Schedule feed','transit'),('gtfs-realtime-feed','GTFS Realtime feed','transit'),('gbfs-feed','GBFS feed','transit'),('transit-feed-coverage','Transit feed coverage','transit') ]}
EVIDENCE_CLASSES={
'open-transport-network-feature':'open network geometry/attribute feature; not guaranteed current, navigable, legally accessible or safe',
'unlocode-location-record':'UN/LOCODE trade/transport location record retaining function and release status; not operating-status proof',
'community-airport-record':'OurAirports community-maintained airport/runway/navigation-aid record; not official aeronautical information',
'mobility-feed-catalog-record':'MobilityData catalog/feed metadata record; not a service guarantee or complete coverage finding'}
def _source(v):
 k=(v or 'overture-transportation').strip().lower()
 if k not in SOURCES: raise ValueError(f'unsupported transportation source: {k}')
 return k,{'id':k,**SOURCES[k]}
def _indicator(v):
 k=(v or 'road-segment').strip().lower()
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
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'evidence_class_count':len(EVIDENCE_CLASSES),'summary':'Orient global transport networks, trade/transport locations, airport/runway records and transit-feed coverage without converting mapping/catalog evidence into navigation, operating-status or safety determinations.','warning':'TRANSPORTATION EVIDENCE · NOT NAVIGATION, OPERATING STATUS OR SAFETY DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'network_segment_equals_navigable_route':False,'network_access_attribute_equals_legal_authorization':False,'unlocode_location_equals_operating_facility':False,'airport_record_equals_official_aeronautical_information':False,'gtfs_feed_equals_service_guarantee':False,'feed_catalog_equals_complete_transit_coverage':False,'zero_records_equals_no_infrastructure':False,'platform_navigation_or_safety_determination':False,'automatic_action_authorized':False}}
def state(source_id='overture-transportation',indicator_type='road-segment',area='',date='',latitude=None,longitude=None):
 _,src=_source(source_id);iid,ind=_indicator(indicator_type)
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':src,'indicator_type':ind,'area':str(area or '').strip() or None,'date':str(date or '').strip() or None,'query_point':_point(latitude,longitude),'source_supports_indicator_type':iid in src['indicator_types'],'evidence':{'network_feature_loaded':False,'trade_transport_location_loaded':False,'airport_record_loaded':False,'transit_feed_record_loaded':False,'official_navigation_record_loaded':False,'live_service_confirmation_loaded':False},'truth':{'network_segment_treated_as_navigable_route':False,'network_access_treated_as_legal_authorization':False,'unlocode_location_treated_as_operating_facility':False,'airport_record_treated_as_official_aeronautical_information':False,'gtfs_feed_treated_as_service_guarantee':False,'feed_catalog_treated_as_complete_transit_coverage':False,'zero_records_treated_as_no_infrastructure':False,'platform_navigation_or_safety_determination':False,'automatic_action_authorized':False}}
def normalize_feature(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id'));iid,_=_indicator(request.get('indicator_type'))
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested transportation indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'source_feature_id':str(request.get('source_feature_id') or '').strip() or None,'source_class':str(request.get('source_class') or '').strip() or None,'source_status':str(request.get('source_status') or '').strip() or None,'release_or_observed_at':str(request.get('release_or_observed_at') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'navigable_route_inferred':False,'operating_status_inferred':False,'legal_access_inferred':False,'capacity_inferred':False,'safety_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'feature':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_feed(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'mobilitydata-database');iid,_=_indicator(request.get('indicator_type') or 'gtfs-schedule-feed')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested transportation indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'feed_id':str(request.get('feed_id') or '').strip() or None,'producer':str(request.get('producer') or '').strip() or None,'service_start':str(request.get('service_start') or '').strip() or None,'service_end':str(request.get('service_end') or '').strip() or None,'quality_status':str(request.get('quality_status') or '').strip() or None,'current_service_inferred':False,'vehicle_arrival_inferred':False,'accessibility_inferred':False,'fare_availability_inferred':False,'complete_coverage_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'feed':r,'record_sha256':_digest(r),'normalized_at':_now()}
def accessibility_preview(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 network_distance=float(request.get('network_distance'));threshold=float(request.get('threshold'));unit=str(request.get('unit') or 'km').strip();direction=str(request.get('direction') or 'within').strip().lower()
 if direction not in {'within','beyond'}: raise ValueError('direction must be within or beyond')
 crossed=network_distance<=threshold if direction=='within' else network_distance>=threshold
 r={'network_distance':network_distance,'threshold':threshold,'unit':unit,'direction':direction,'screening_condition_met':crossed,'actual_travel_time_determined':False,'route_operability_determined':False,'legal_access_determined':False,'transit_service_determined':False,'emergency_access_determined':False,'navigation_instruction_issued':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='overture-transportation',indicator_type='road-segment',area='',date='',latitude=None,longitude=None):
 cur=state(source_id,indicator_type,area,date,latitude,longitude);p={'schema':'sc-site-intelligence-transportation/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'area':cur['area'],'date':cur['date'],'query_point':cur['query_point']},'evidence':cur['evidence'],'review':{'network_segment_as_navigable_route':False,'network_access_as_legal_authorization':False,'unlocode_as_operating_facility':False,'airport_record_as_official_aeronautical_information':False,'gtfs_as_service_guarantee':False,'feed_catalog_as_complete_coverage':False,'zero_records_as_no_infrastructure':False,'platform_navigation_or_safety_determination':False}}
 return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
 c={'four_source_families_registered':len(SOURCES)==4,'overture_registered':'overture-transportation' in SOURCES,'unlocode_registered':'unece-unlocode' in SOURCES,'ourairports_registered':'ourairports' in SOURCES,'mobility_database_registered':'mobilitydata-database' in SOURCES,'navigation_guard_present':True,'operating_status_guard_present':True,'service_guarantee_guard_present':True,'aeronautical_safety_guard_present':True,'public_route_count_preserved':True}
 return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
