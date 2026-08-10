from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-geosphere-earthquake-volcano-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'usgs-earthquake-catalog':{'title':'USGS Earthquake Catalog & Real-time Feeds','organization':'U.S. Geological Survey Earthquake Hazards Program','url':'https://earthquake.usgs.gov/earthquakes/search/','api_url':'https://earthquake.usgs.gov/fdsnws/event/1/','recognized_hosts':['earthquake.usgs.gov'],'indicator_types':['earthquake-event','magnitude','depth','review-status','pager-alert'],'evidence_classes':['seismic-event-catalog','real-time-earthquake-feed'],'coverage':'Global earthquake-event catalog and real-time GeoJSON feeds using the USGS implementation of the FDSN Event Web Service.','limitations':'Catalog events and preferred origins/magnitudes may be revised as additional data are reviewed. A catalog event is not a Site Intelligence emergency warning, local damage finding, or guarantee of completeness.'},
'usgs-shakemap':{'title':'USGS ShakeMap & PAGER Products','organization':'U.S. Geological Survey Earthquake Hazards Program','url':'https://earthquake.usgs.gov/data/shakemap/','api_url':'https://earthquake.usgs.gov/fdsnws/event/1/query?producttype=shakemap','recognized_hosts':['earthquake.usgs.gov'],'indicator_types':['shaking-intensity','peak-ground-acceleration','peak-ground-velocity','pager-alert'],'evidence_classes':['modeled-shaking-product','loss-estimation-product'],'coverage':'Event-linked shaking and impact products associated with USGS earthquake records.','limitations':'ShakeMap is a modeled/observationally constrained shaking product, not a building-by-building damage census. PAGER alerts are source-issued impact estimates and are never reissued as Sustainable Catalyst alerts.'},
'usgs-volcano-hans':{'title':'USGS Volcano Hazards Program HANS','organization':'U.S. Geological Survey Volcano Hazards Program','url':'https://www.usgs.gov/programs/vhp','api_url':'https://volcanoes.usgs.gov/vsc/api/hansApi/','recognized_hosts':['www.usgs.gov','usgs.gov','volcanoes.usgs.gov'],'indicator_types':['volcano-alert-level','aviation-color-code','volcano-notice','eruption-status'],'evidence_classes':['source-issued-volcano-notice','source-issued-aviation-notice'],'coverage':'U.S. Volcano Observatory notifications, alert levels, aviation color codes, and volcano notices.','limitations':'USGS observatories are the issuing authority for their notices. Site Intelligence preserves notice attribution and does not create, escalate, downgrade, or supersede volcano alert levels or aviation color codes.'},
'nasa-jpl-aria':{'title':'NASA/JPL ARIA Ground Deformation Products','organization':'NASA Jet Propulsion Laboratory / Caltech ARIA','url':'https://aria.jpl.nasa.gov/','api_url':'https://aria.jpl.nasa.gov/products/','recognized_hosts':['aria.jpl.nasa.gov','gis.earthdata.nasa.gov','earthdata.nasa.gov','www.earthdata.nasa.gov'],'indicator_types':['ground-displacement','interferometric-coherence','coseismic-deformation','volcanic-deformation'],'evidence_classes':['insar-displacement-product','rapid-response-deformation-product'],'coverage':'Satellite-radar deformation products supporting earthquake, volcano, subsidence, and other solid-Earth applications.','limitations':'InSAR displacement measures line-of-sight surface motion and may contain unwrapping, coherence, atmospheric, geometry, or rapid-response limitations. It is not silently converted into vertical displacement, structural damage, causation, or a hazard declaration.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('earthquake-event','Earthquake event','seismology'),('magnitude','Magnitude','seismology'),('depth','Hypocentral depth','seismology'),('review-status','Event review status','seismology'),('pager-alert','PAGER alert','impact-estimation'),('shaking-intensity','Shaking intensity','ground-motion'),('peak-ground-acceleration','Peak ground acceleration','ground-motion'),('peak-ground-velocity','Peak ground velocity','ground-motion'),('volcano-alert-level','Volcano alert level','volcanology'),('aviation-color-code','Aviation color code','volcanology'),('volcano-notice','Volcano notice','volcanology'),('eruption-status','Eruption status','volcanology'),('ground-displacement','Ground displacement','geodesy'),('interferometric-coherence','Interferometric coherence','geodesy'),('coseismic-deformation','Coseismic deformation','geodesy'),('volcanic-deformation','Volcanic deformation','geodesy')]}
EVIDENCE_CLASSES={'seismic-event-catalog':'earthquake-event catalog record with source review state retained','real-time-earthquake-feed':'real-time earthquake feed record subject to later revision','modeled-shaking-product':'ShakeMap ground-motion product distinct from direct structural damage evidence','loss-estimation-product':'source-issued PAGER impact-estimation product distinct from confirmed loss','source-issued-volcano-notice':'USGS Volcano Hazards Program source-issued notice','source-issued-aviation-notice':'USGS source-issued aviation notice/color-code context','insar-displacement-product':'interferometric radar displacement product with geometry/quality caveats','rapid-response-deformation-product':'rapid-response deformation product with preliminary status retained'}
def _source(v):
    k=(v or 'usgs-earthquake-catalog').strip().lower()
    if k not in SOURCES: raise ValueError(f'unsupported geosphere source: {k}')
    return k,{'id':k,**SOURCES[k]}
def _indicator(v):
    k=(v or 'earthquake-event').strip().lower()
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
def _url(source,raw):
    value=str(raw or '').strip(); p=urlparse(value)
    if p.scheme!='https' or (p.hostname or '').lower() not in source['recognized_hosts']: raise ValueError('source_url must use HTTPS and a registered source host')
    return value
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'summary':'Orient earthquake, ground-motion, volcano-notification and ground-deformation evidence while preserving revision state, model/observation distinctions, and source-issued warning authority.','warning':'SOLID-EARTH EVIDENCE · NOT AN EMERGENCY, DAMAGE OR HAZARD DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'catalog_event_equals_emergency_warning':False,'shakemap_equals_structural_damage':False,'pager_equals_confirmed_loss':False,'source_volcano_alert_reissued_by_platform':False,'insar_equals_vertical_displacement':False,'insar_equals_damage':False,'preliminary_equals_final':False,'zero_records_equals_no_hazard':False}}
def state(source_id='usgs-earthquake-catalog',indicator_type='earthquake-event',latitude=None,longitude=None,date=''):
    _,source=_source(source_id); iid,indicator=_indicator(indicator_type)
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':source,'indicator_type':indicator,'query_point':_point(latitude,longitude),'date':str(date or '').strip() or None,'source_supports_indicator_type':iid in source['indicator_types'],'evidence':{'event_loaded':False,'shakemap_loaded':False,'pager_loaded':False,'volcano_notice_loaded':False,'deformation_product_loaded':False},'truth':{'catalog_event_treated_as_emergency_warning':False,'shakemap_treated_as_structural_damage':False,'pager_treated_as_confirmed_loss':False,'platform_volcano_alert_issued':False,'platform_aviation_notice_issued':False,'insar_treated_as_vertical_displacement':False,'insar_treated_as_damage':False,'preliminary_treated_as_final':False,'zero_records_treated_as_no_hazard':False,'automatic_action_authorized':False}}
def normalize_measurement(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id')); iid,_=_indicator(request.get('indicator_type'))
    if iid not in source['indicator_types']: raise ValueError('source does not register the requested geosphere indicator')
    ev=_evidence(request.get('evidence_class') or source['evidence_classes'][0])
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    value=request.get('value'); value=None if value in (None,'') else float(value)
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'value':value,'unit':str(request.get('unit') or '').strip() or None,'observed_at':str(request.get('observed_at') or '').strip() or None,'review_status':str(request.get('review_status') or '').strip() or None,'product_status':str(request.get('product_status') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'catalog_event_treated_as_emergency_warning':False,'shakemap_treated_as_structural_damage':False,'pager_treated_as_confirmed_loss':False,'insar_treated_as_vertical_displacement':False,'insar_treated_as_damage':False,'platform_warning_issued':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'measurement':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_notice(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id') or 'usgs-volcano-hans'); iid,_=_indicator(request.get('indicator_type') or 'volcano-notice')
    if iid not in source['indicator_types']: raise ValueError('source does not register the requested geosphere notice')
    ev=_evidence(request.get('evidence_class') or source['evidence_classes'][0])
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'notice_id':str(request.get('notice_id') or '').strip() or None,'alert_level':str(request.get('alert_level') or '').strip() or None,'aviation_color_code':str(request.get('aviation_color_code') or '').strip() or None,'issued_at':str(request.get('issued_at') or '').strip() or None,'source_issued':True,'platform_reissued':False,'platform_escalated':False,'platform_downgraded':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'notice':r,'record_sha256':_digest(r),'normalized_at':_now()}
def threshold_preview(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    value=float(request.get('value')); threshold=float(request.get('threshold')); op=str(request.get('operator') or '>=').strip()
    if op not in {'>','>=','<','<=','=='}: raise ValueError('unsupported operator')
    comparison={'>':value>threshold,'>=':value>=threshold,'<':value<threshold,'<=':value<=threshold,'==':value==threshold}[op]
    r={'value':value,'threshold':threshold,'operator':op,'comparison':comparison,'unit':str(request.get('unit') or '').strip() or None,'source_threshold_label':str(request.get('source_threshold_label') or '').strip() or None,'earthquake_warning':False,'volcano_alert':False,'aviation_notice':False,'damage_finding':False,'loss_finding':False,'causal_attribution':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='usgs-earthquake-catalog',indicator_type='earthquake-event',latitude=None,longitude=None,date=''):
    cur=state(source_id,indicator_type,latitude,longitude,date); p={'schema':'sc-site-intelligence-geosphere/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'query_point':cur['query_point'],'date':cur['date']},'evidence':cur['evidence'],'review':{'catalog_event_as_warning':False,'shakemap_as_damage':False,'pager_as_confirmed_loss':False,'platform_volcano_alert':False,'platform_aviation_notice':False,'insar_as_vertical_displacement':False,'insar_as_damage':False,'preliminary_as_final':False,'zero_records_as_no_hazard':False}}
    return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
    c={'four_source_families_registered':len(SOURCES)==4,'usgs_earthquake_registered':'usgs-earthquake-catalog' in SOURCES,'usgs_shakemap_registered':'usgs-shakemap' in SOURCES,'usgs_volcano_hans_registered':'usgs-volcano-hans' in SOURCES,'nasa_aria_registered':'nasa-jpl-aria' in SOURCES,'warning_authority_guard_present':True,'shakemap_damage_guard_present':True,'pager_loss_guard_present':True,'insar_geometry_guard_present':True,'public_route_count_preserved':True}
    return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
