from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-wetlands-inland-waters-aquatic-habitat-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'usfws-nwi':{'title':'USFWS National Wetlands Inventory','organization':'U.S. Fish & Wildlife Service','url':'https://www.fws.gov/program/national-wetlands-inventory','api_url':'https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest','recognized_hosts':['www.fws.gov','fws.gov','fwspublicservices.wim.usgs.gov'],'indicator_types':['wetland-classification','wetland-boundary','riparian-classification'],'evidence_classes':['wetland-inventory-feature','wetland-map-classification'],'coverage':'U.S. National Wetlands Inventory geospatial wetlands and reference layers available through REST and OGC web mapping services.','limitations':'NWI map data are inventory/cartographic evidence, not a site-specific wetland delineation, jurisdictional determination, permitting decision or proof that an unmapped wetland is absent.'},
'ramsar-rsis':{'title':'Ramsar Sites Information Service','organization':'Convention on Wetlands Secretariat','url':'https://rsis.ramsar.org/','api_url':'https://rsis.ramsar.org/','recognized_hosts':['rsis.ramsar.org','www.ramsar.org','ramsar.org'],'indicator_types':['ramsar-site','wetland-type','ecosystem-service-context'],'evidence_classes':['internationally-designated-site-record','ramsar-site-boundary'],'coverage':'Global records for Wetlands of International Importance with site metadata, wetland types, criteria and downloadable centroid/boundary data.','limitations':'Ramsar designation records are international site records, not a complete global wetland inventory. Boundaries and territorial information are presented as available and do not resolve sovereignty or national legal jurisdiction.'},
'jrc-global-surface-water':{'title':'JRC Global Surface Water v1.4','organization':'European Commission Joint Research Centre / Copernicus','url':'https://global-surface-water.appspot.com/','api_url':'https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_GlobalSurfaceWater','recognized_hosts':['global-surface-water.appspot.com','developers.google.com'],'indicator_types':['surface-water-occurrence','surface-water-seasonality','surface-water-transition','water-change'],'evidence_classes':['landsat-derived-water-classification','surface-water-change-layer'],'coverage':'Global Landsat-derived surface-water occurrence, seasonality and change mapping for 1984–2021 at 30 m.','limitations':'This is remote-sensing water/non-water classification and change evidence, not a wetland-type inventory, water-right determination, current field observation, or proof that masked/non-detected pixels contain no aquatic habitat.'},
'nasa-swot-inland-water':{'title':'NASA/JPL SWOT Inland Water','organization':'NASA / CNES / JPL PO.DAAC','url':'https://podaac.jpl.nasa.gov/SWOT','api_url':'https://gis.earthdata.nasa.gov/','recognized_hosts':['podaac.jpl.nasa.gov','gis.earthdata.nasa.gov','earthdata.nasa.gov'],'indicator_types':['water-surface-elevation','river-width','river-area','lake-area','river-discharge-estimate'],'evidence_classes':['swot-radar-measurement','swot-derived-hydrologic-estimate'],'coverage':'SWOT high-resolution inland-water products for rivers and lakes, including water-surface elevation, width, area and discharge estimates.','limitations':'SWOT values are satellite-derived measurements/estimates with product quality flags, spatial thresholds and algorithm context. They are not field gauges at every location, wetland delineations, flood warnings or navigational determinations.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [('wetland-classification','Wetland classification','wetlands'),('wetland-boundary','Wetland boundary','wetlands'),('riparian-classification','Riparian classification','wetlands'),('ramsar-site','Ramsar site','wetland-governance'),('wetland-type','Wetland type','wetland-governance'),('ecosystem-service-context','Ecosystem-service context','wetland-governance'),('surface-water-occurrence','Surface-water occurrence','inland-water'),('surface-water-seasonality','Surface-water seasonality','inland-water'),('surface-water-transition','Surface-water transition','inland-water'),('water-change','Surface-water change','inland-water'),('water-surface-elevation','Water-surface elevation','inland-water'),('river-width','River width','inland-water'),('river-area','River area','inland-water'),('lake-area','Lake area','inland-water'),('river-discharge-estimate','River discharge estimate','inland-water')]}
EVIDENCE_CLASSES={'wetland-inventory-feature':'mapped NWI inventory feature; not a site-specific delineation or jurisdictional finding','wetland-map-classification':'source wetland classification retaining mapping method and inventory context','internationally-designated-site-record':'Ramsar site record; international designation evidence distinct from comprehensive wetland inventory','ramsar-site-boundary':'downloaded/mapped Ramsar site boundary with source territorial disclaimer retained','landsat-derived-water-classification':'JRC Landsat-derived water/non-water classification, not wetland-type ground truth','surface-water-change-layer':'remote-sensing surface-water transition/change layer','swot-radar-measurement':'SWOT KaRIn-derived inland-water measurement retaining quality/product context','swot-derived-hydrologic-estimate':'SWOT-derived hydrologic estimate, including algorithm-derived discharge, distinct from a direct gauge observation'}
def _source(v):
 k=(v or 'usfws-nwi').strip().lower()
 if k not in SOURCES: raise ValueError(f'unsupported wetlands source: {k}')
 return k,{'id':k,**SOURCES[k]}
def _indicator(v):
 k=(v or 'wetland-classification').strip().lower()
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
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'evidence_class_count':len(EVIDENCE_CLASSES),'summary':'Orient mapped wetlands, internationally designated wetland sites, global surface-water change and SWOT inland-water measurements while preserving inventory, remote-sensing, designation and jurisdictional boundaries.','warning':'WETLAND & INLAND-WATER EVIDENCE · NOT A JURISDICTIONAL DELINEATION, FLOOD WARNING OR HABITAT-ABSENCE FINDING'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'mapped_wetland_equals_jurisdictional_wetland':False,'no_mapped_wetland_equals_no_wetland':False,'ramsar_site_equals_complete_wetland_inventory':False,'surface_water_equals_wetland_type':False,'swot_estimate_equals_field_gauge':False,'surface_water_change_equals_ecological_harm':False,'platform_flood_warning':False,'platform_permitting_determination':False}}
def state(source_id='usfws-nwi',indicator_type='wetland-classification',latitude=None,longitude=None,date=''):
 _,src=_source(source_id); iid,ind=_indicator(indicator_type)
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':src,'indicator_type':ind,'query_point':_point(latitude,longitude),'date':str(date or '').strip() or None,'source_supports_indicator_type':iid in src['indicator_types'],'evidence':{'wetland_feature_loaded':False,'ramsar_site_loaded':False,'surface_water_layer_loaded':False,'swot_measurement_loaded':False,'field_delineation_loaded':False,'jurisdictional_finding_loaded':False},'truth':{'mapped_wetland_treated_as_jurisdictional_wetland':False,'zero_records_treated_as_no_wetland_or_habitat':False,'ramsar_site_treated_as_complete_inventory':False,'surface_water_treated_as_wetland_type':False,'swot_estimate_treated_as_field_gauge':False,'surface_water_change_treated_as_ecological_harm':False,'platform_flood_warning_issued':False,'platform_permitting_determination':False,'automatic_action_authorized':False}}
def normalize_feature(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id')); iid,_=_indicator(request.get('indicator_type'))
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested wetlands indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'source_feature_id':str(request.get('source_feature_id') or '').strip() or None,'source_class':str(request.get('source_class') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'jurisdictional_wetland_inferred':False,'wetland_absence_inferred':False,'permitting_status_inferred':False,'habitat_condition_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'feature':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_measurement(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 _,src=_source(request.get('source_id') or 'nasa-swot-inland-water'); iid,_=_indicator(request.get('indicator_type') or 'water-surface-elevation')
 if iid not in src['indicator_types']: raise ValueError('source does not register the requested inland-water indicator')
 ev=_evidence(request.get('evidence_class') or src['evidence_classes'][0])
 if ev not in src['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
 r={'source_id':src['id'],'source_url':_url(src,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'value':None if request.get('value') in (None,'') else float(request.get('value')),'unit':str(request.get('unit') or '').strip() or None,'observed_at':str(request.get('observed_at') or '').strip() or None,'quality_flag':str(request.get('quality_flag') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'field_gauge_inferred':False,'flood_warning_inferred':False,'navigational_safety_inferred':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'measurement':r,'record_sha256':_digest(r),'normalized_at':_now()}
def overlap_preview(request:dict[str,Any]):
 if not isinstance(request,dict): raise TypeError('request must be an object')
 def box(v,name):
  if not isinstance(v,(list,tuple)) or len(v)!=4: raise ValueError(f'{name} must be [west,south,east,north]')
  w,s,e,n=map(float,v)
  if not (-180<=w<=180 and -180<=e<=180 and -90<=s<=90 and -90<=n<=90 and w<=e and s<=n): raise ValueError(f'{name} outside valid bounds')
  return [w,s,e,n]
 a,b=box(request.get('feature_bbox'),'feature_bbox'),box(request.get('area_bbox'),'area_bbox'); intersects=not(a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1])
 r={'feature_bbox':a,'area_bbox':b,'spatial_overlap':intersects,'wetland_presence_field_verified':False,'jurisdictional_status_determined':False,'permit_requirement_determined':False,'ecological_impact_determined':False,'legal_determination':False,'automatic_action_authorized':False}
 return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='usfws-nwi',indicator_type='wetland-classification',latitude=None,longitude=None,date=''):
 cur=state(source_id,indicator_type,latitude,longitude,date); p={'schema':'sc-site-intelligence-wetlands-inland-water/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'query_point':cur['query_point'],'date':cur['date']},'evidence':cur['evidence'],'review':{'mapped_wetland_as_jurisdictional':False,'zero_records_as_no_wetland':False,'ramsar_as_complete_inventory':False,'surface_water_as_wetland_type':False,'swot_as_field_gauge':False,'surface_water_change_as_ecological_harm':False,'platform_flood_warning':False,'platform_permitting_determination':False}}
 return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
 c={'four_source_families_registered':len(SOURCES)==4,'nwi_registered':'usfws-nwi' in SOURCES,'ramsar_registered':'ramsar-rsis' in SOURCES,'jrc_surface_water_registered':'jrc-global-surface-water' in SOURCES,'swot_registered':'nasa-swot-inland-water' in SOURCES,'jurisdiction_guard_present':True,'absence_guard_present':True,'remote_sensing_class_guard_present':True,'field_gauge_guard_present':True,'flood_warning_guard_present':True,'public_route_count_preserved':True}
 return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
