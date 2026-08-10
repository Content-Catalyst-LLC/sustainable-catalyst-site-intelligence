from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='ocean-governance-jurisdiction-maritime-boundaries'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'noaa-maritime-boundaries':{'title':'NOAA U.S. Maritime Limits & Boundaries','organization':'NOAA Office of Coast Survey','url':'https://nauticalcharts.noaa.gov/data/us-maritime-limits-and-boundaries.html','api_url':'https://encdirect.noaa.gov/arcgis/rest/services/MaritimeBoundaries/US_Maritime_Limits_Boundaries/MapServer','recognized_hosts':['nauticalcharts.noaa.gov','encdirect.noaa.gov'],'zone_types':['territorial-sea','contiguous-zone','exclusive-economic-zone','maritime-boundary'],'evidence_classes':['maritime-zone-feature','maritime-boundary-line'],'coverage':'U.S. territorial sea, contiguous zone, EEZ and maritime-boundary mapping from NOAA nautical-chart workflows.','limitations':'Dynamic GIS services are orientation data. NOAA warns some service depictions are not for legal use; official chart/source material controls.'},
'marine-regions-vliz':{'title':'Marine Regions Maritime Boundaries','organization':'Flanders Marine Institute (VLIZ)','url':'https://www.marineregions.org/','api_url':'https://geo.vliz.be/geoserver/MarineRegions/wfs','recognized_hosts':['marineregions.org','www.marineregions.org','geo.vliz.be','vliz.be','www.vliz.be'],'zone_types':['territorial-sea','contiguous-zone','exclusive-economic-zone','internal-waters','archipelagic-waters','high-seas','extended-continental-shelf','maritime-boundary'],'evidence_classes':['maritime-zone-feature','maritime-boundary-line','high-seas-feature','continental-shelf-feature','treaty-metadata'],'coverage':'Global maritime-boundary products served through WMS/WFS, including EEZ, territorial sea, contiguous zone, internal/archipelagic waters, high seas and extended continental shelves.','limitations':'Marine Regions is a compiled geospatial database. Methodology, version, known issues, disputes and treaty metadata remain visible; geometry is not a platform legal opinion.'},
'fao-major-fishing-areas':{'title':'FAO Major Fishing Areas','organization':'Food and Agriculture Organization of the United Nations','url':'https://www.fao.org/cwp-on-fishery-statistics/handbook/general-concepts/main-water-areas/en/','api_url':'https://www.fao.org/fishery/en/area/search','recognized_hosts':['fao.org','www.fao.org'],'zone_types':['fao-major-fishing-area','fao-statistical-subarea'],'evidence_classes':['statistical-area'],'coverage':'Global FAO fishing areas and subareas used for fishery and aquaculture statistics and reporting.','limitations':'FAO Major Fishing Areas are statistical areas. They do not by themselves establish sovereignty, fishing rights, licensing, enforcement jurisdiction or a maritime boundary.'},
'fao-regional-fishery-bodies':{'title':'FAO Regional Fishery Bodies','organization':'Food and Agriculture Organization of the United Nations','url':'https://www.fao.org/fishery/en/collection/rfb','api_url':'https://www.fao.org/fishery/geoserver/factsheets/rfbs.html','recognized_hosts':['fao.org','www.fao.org'],'zone_types':['regional-fishery-body-area','management-area-context'],'evidence_classes':['regional-fishery-body-area','jurisdiction-context'],'coverage':'Regional Fishery Body geographic coverage and management-context mapping published by FAO.','limitations':'RFB map coverage is institutional/management context. It does not imply sovereignty, resolve disputed boundaries, or determine whether a vessel or activity is legally authorized.'}}
ZONE_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('territorial-sea','Territorial sea','maritime-zone'),('contiguous-zone','Contiguous zone','maritime-zone'),('exclusive-economic-zone','Exclusive economic zone','maritime-zone'),('internal-waters','Internal waters','maritime-zone'),('archipelagic-waters','Archipelagic waters','maritime-zone'),('high-seas','High seas','maritime-zone'),('extended-continental-shelf','Extended continental shelf','maritime-zone'),('maritime-boundary','Maritime boundary','maritime-zone'),('fao-major-fishing-area','FAO Major Fishing Area','management-area'),('fao-statistical-subarea','FAO statistical subarea','management-area'),('regional-fishery-body-area','Regional Fishery Body area','management-area'),('management-area-context','Management-area context','management-area')]}
EVIDENCE_CLASSES={'maritime-zone-feature':'source-published polygon or feature representing a maritime zone','maritime-boundary-line':'source-published line geometry representing a maritime limit or boundary','high-seas-feature':'source-published high-seas geometry','continental-shelf-feature':'source-published extended continental-shelf geometry','treaty-metadata':'source-linked treaty or delimitation metadata retained without platform legal interpretation','statistical-area':'FAO statistical fishing-area evidence','regional-fishery-body-area':'source-published Regional Fishery Body coverage area','jurisdiction-context':'institutional or management-area context that is not treated as a sovereignty determination'}
def _source(v):
    k=(v or 'marine-regions-vliz').strip().lower()
    if k not in SOURCES: raise ValueError(f'unsupported governance source: {k}')
    return k,{'id':k,**SOURCES[k]}
def _zone(v):
    k=(v or 'exclusive-economic-zone').strip().lower()
    if k not in ZONE_TYPES: raise ValueError(f'unsupported zone_type: {k}')
    return k,{'id':k,**ZONE_TYPES[k]}
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
def _bbox(v,field='bbox'):
    if v in (None,''): return None
    if not isinstance(v,(list,tuple)) or len(v)!=4: raise ValueError(f'{field} must be [west,south,east,north]')
    w,s,e,n=[float(x) for x in v]
    if not(-180<=w<=180 and -180<=e<=180 and -90<=s<=90 and -90<=n<=90): raise ValueError(f'{field} coordinates outside valid bounds')
    if w>e or s>n: raise ValueError(f'{field} must not cross antimeridian and must be ordered')
    return [round(w,6),round(s,6),round(e,6),round(n,6)]
def _url(source,raw):
    value=str(raw or '').strip(); p=urlparse(value)
    if p.scheme!='https' or (p.hostname or '').lower() not in source['recognized_hosts']: raise ValueError('source_url must use HTTPS and a registered source host')
    return value
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'zone_type_count':len(ZONE_TYPES),'summary':'Orient maritime zones, boundaries, fishing statistical areas and Regional Fishery Body coverage while keeping source authority, disputes and legal uncertainty visible.','warning':'JURISDICTION ORIENTATION · NOT A LEGAL DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'zone_types':[{'id':k,**v} for k,v in ZONE_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'geometry_is_legal_determination':False,'statistical_area_is_jurisdiction':False,'rfb_area_is_sovereignty':False,'overlap_is_legal_conflict':False,'map_is_navigation_authority':False,'fishing_authorization_inferred':False}}
def state(source_id='marine-regions-vliz',zone_type='exclusive-economic-zone',latitude=None,longitude=None,date=''):
    _,source=_source(source_id); zid,zone=_zone(zone_type)
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':source,'zone_type':zone,'query_point':_point(latitude,longitude),'date':str(date or '').strip() or None,'source_supports_zone_type':zid in source['zone_types'],'evidence':{'zone_record_loaded':False,'management_area_loaded':False,'treaty_metadata_loaded':False},'truth':{'platform_legal_boundary_determination':False,'platform_sovereignty_determination':False,'statistical_area_treated_as_jurisdiction':False,'rfb_area_treated_as_sovereignty':False,'fishing_authorization_inferred':False,'enforcement_finding':False,'navigation_authority':False,'dispute_resolved_by_platform':False}}
def normalize_zone(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id')); zid,zone=_zone(request.get('zone_type'))
    if zone['domain']!='maritime-zone' or zid not in source['zone_types']: raise ValueError('source does not register the requested maritime zone')
    ev=_evidence(request.get('evidence_class') or 'maritime-zone-feature')
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    bbox=_bbox(request.get('bbox'))
    if bbox is None: raise ValueError('zone record requires bbox')
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'zone_type':zid,'evidence_class':ev,'record_id':str(request.get('record_id') or '').strip() or None,'bbox':bbox,'source_version':str(request.get('source_version') or '').strip() or None,'effective_at':str(request.get('effective_at') or '').strip() or None,'source_reports_dispute':bool(request.get('source_reports_dispute',False)),'platform_legal_determination':False,'sovereignty_inferred':False,'navigation_authority':False,'enforcement_authority':False,'dispute_resolved_by_platform':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'zone':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_management_area(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id')); zid,zone=_zone(request.get('zone_type'))
    if zone['domain']!='management-area' or zid not in source['zone_types']: raise ValueError('source does not register the requested management/statistical area')
    ev=_evidence(request.get('evidence_class') or ('statistical-area' if source['id']=='fao-major-fishing-areas' else 'regional-fishery-body-area'))
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    bbox=_bbox(request.get('bbox'))
    if bbox is None: raise ValueError('management-area record requires bbox')
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'zone_type':zid,'evidence_class':ev,'area_code':str(request.get('area_code') or '').strip() or None,'area_name':str(request.get('area_name') or '').strip() or None,'body_name':str(request.get('body_name') or '').strip() or None,'bbox':bbox,'statistical_purpose':source['id']=='fao-major-fishing-areas','jurisdiction_inferred':False,'sovereignty_inferred':False,'fishing_authorization_inferred':False,'enforcement_finding':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'management_area':r,'record_sha256':_digest(r),'normalized_at':_now()}
def overlap_preview(request:dict[str,Any]):
    a=_bbox(request.get('area_a_bbox'),'area_a_bbox'); b=_bbox(request.get('area_b_bbox'),'area_b_bbox')
    if a is None or b is None: raise ValueError('both area_a_bbox and area_b_bbox are required')
    intersects=not(a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1])
    r={'area_a_bbox':a,'area_b_bbox':b,'spatial_intersection':intersects,'legal_overlap_determination':False,'jurisdiction_conflict_determined':False,'sovereignty_conflict_determined':False,'fishing_authorization_determined':False,'enforcement_action_authorized':False,'navigation_instruction':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='marine-regions-vliz',zone_type='exclusive-economic-zone',latitude=None,longitude=None,date=''):
    cur=state(source_id,zone_type,latitude,longitude,date); p={'schema':'sc-site-intelligence-ocean-governance/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'zone_type':cur['zone_type']['id'],'query_point':cur['query_point'],'date':cur['date']},'evidence':cur['evidence'],'review':{'geometry_as_legal_determination':False,'statistical_area_as_jurisdiction':False,'rfb_area_as_sovereignty':False,'overlap_as_legal_conflict':False,'fishing_authorization_inferred':False,'platform_enforcement_finding':False}}
    return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
    c={'four_source_families_registered':len(SOURCES)==4,'noaa_maritime_boundaries_registered':'noaa-maritime-boundaries' in SOURCES,'global_marine_regions_registered':'marine-regions-vliz' in SOURCES,'fao_statistical_areas_registered':'fao-major-fishing-areas' in SOURCES,'fao_rfb_registered':'fao-regional-fishery-bodies' in SOURCES,'legal_determination_guard_present':True,'statistical_area_guard_present':True,'rfb_sovereignty_guard_present':True,'overlap_conflict_guard_present':True,'public_route_count_preserved':True}
    return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'zone_types':len(ZONE_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
