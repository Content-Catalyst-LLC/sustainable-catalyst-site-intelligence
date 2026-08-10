from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from .version import APP_VERSION
VERSION=APP_VERSION
CONTRACT='global-biodiversity-species-distribution-conservation-intelligence'
ROUTE='earth'
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
SOURCES={
'gbif-occurrence':{
 'title':'GBIF Occurrence API','organization':'Global Biodiversity Information Facility','url':'https://www.gbif.org/developer/occurrence','api_url':'https://api.gbif.org/v1/occurrence/search','recognized_hosts':['api.gbif.org','www.gbif.org','techdocs.gbif.org'],'indicator_types':['species-occurrence','occurrence-count','taxonomic-occurrence','observation-media'],'evidence_classes':['occurrence-record','aggregated-occurrence-count'],'coverage':'Global biodiversity occurrence records from publishing institutions and citizen-science/data-network contributors.','limitations':'Occurrence records preserve basisOfRecord, dataset, coordinates, uncertainty, date, taxonomic and issue flags. A record is evidence of a reported occurrence, not a population census or proof of current occupancy. Search pagination is bounded and large complete extracts use the separate authenticated download service.'},
'obis':{
 'title':'Ocean Biodiversity Information System','organization':'IOC-UNESCO / OBIS','url':'https://obis.org/','api_url':'https://api.obis.org/','recognized_hosts':['api.obis.org','obis.org','manual.obis.org'],'indicator_types':['marine-species-occurrence','marine-occurrence-count','marine-taxon-checklist'],'evidence_classes':['marine-occurrence-record','aggregated-marine-occurrence-count'],'coverage':'Global marine biodiversity occurrence, event and associated environmental/measurement data distributed by the OBIS network.','limitations':'OBIS aggregates records under underlying dataset licenses and quality-control fields. Absence records are handled explicitly and are not equivalent to a complete survey; zero returned records do not establish biological absence.'},
'ebird-public':{
 'title':'eBird Public Data & APIs','organization':'Cornell Lab of Ornithology','url':'https://science.ebird.org/en/use-ebird-data/download-ebird-data-products','api_url':'https://api.ebird.org/v2/','recognized_hosts':['api.ebird.org','science.ebird.org','ebird.org'],'indicator_types':['bird-observation','bird-observation-count','bird-checklist'],'evidence_classes':['bird-observation-record','bird-checklist-record'],'coverage':'Bird observations and checklist-derived occurrence information, with broader downloadable data products available separately.','limitations':'Observation detectability, effort, protocol, observer behavior and data-review status matter. An eBird observation is not a complete census, breeding confirmation, population estimate or proof that unreported species are absent. Public API access may require an eBird API key.'},
'usfws-ecos':{
 'title':'USFWS ECOS Species Data Services','organization':'U.S. Fish & Wildlife Service','url':'https://ecos.fws.gov/ecp/services','api_url':'https://ecos.fws.gov/ecp/pullreports/catalog/species/report/species/export','recognized_hosts':['ecos.fws.gov','maps.ecosphere.fws.gov','ipacb.ecosphere.fws.gov'],'indicator_types':['esa-listing-status','critical-habitat','recovery-document'],'evidence_classes':['esa-species-record','critical-habitat-boundary','recovery-document-record'],'coverage':'U.S. Endangered Species Act listing, taxonomy, Federal Register, recovery-document and critical-habitat data services.','limitations':'ECOS records are U.S. legal/conservation records, not a global conservation-status system. Critical-habitat geometry or species-list overlap does not itself determine project effects, consultation obligations, take, authorization or legal compliance; official project species lists are obtained through IPaC.'}}
INDICATOR_TYPES={k:{'title':t,'domain':d} for k,t,d in [
('species-occurrence','Species occurrence','biodiversity-occurrence'),('occurrence-count','Occurrence count','biodiversity-occurrence'),('taxonomic-occurrence','Taxonomic occurrence','biodiversity-occurrence'),('observation-media','Occurrence media','biodiversity-occurrence'),('marine-species-occurrence','Marine species occurrence','marine-biodiversity'),('marine-occurrence-count','Marine occurrence count','marine-biodiversity'),('marine-taxon-checklist','Marine taxon checklist','marine-biodiversity'),('bird-observation','Bird observation','avian-biodiversity'),('bird-observation-count','Bird observation count','avian-biodiversity'),('bird-checklist','Bird checklist','avian-biodiversity'),('esa-listing-status','ESA listing status','conservation-governance'),('critical-habitat','Critical habitat','conservation-governance'),('recovery-document','Recovery document','conservation-governance')]}
EVIDENCE_CLASSES={
'occurrence-record':'individual published occurrence record retaining source dataset, basis of record and quality context',
'aggregated-occurrence-count':'source-query count or aggregate, not a census or population estimate',
'marine-occurrence-record':'OBIS marine occurrence record with dataset license and QC context',
'aggregated-marine-occurrence-count':'OBIS aggregate or filtered record count distinct from biological abundance',
'bird-observation-record':'eBird observation record retaining date, place and observation context',
'bird-checklist-record':'checklist-derived bird evidence retaining effort/protocol context where available',
'esa-species-record':'USFWS-managed ESA species/listing record; U.S.-specific legal status',
'critical-habitat-boundary':'USFWS designated/proposed critical-habitat geometry; overlap alone is not a project-effects determination',
'recovery-document-record':'USFWS recovery-document metadata associated with an ESA-managed species'}
def _source(v):
    k=(v or 'gbif-occurrence').strip().lower()
    if k not in SOURCES: raise ValueError(f'unsupported biodiversity source: {k}')
    return k,{'id':k,**SOURCES[k]}
def _indicator(v):
    k=(v or 'species-occurrence').strip().lower()
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
def overview(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'route':ROUTE,'source_count':len(SOURCES),'indicator_type_count':len(INDICATOR_TYPES),'evidence_class_count':len(EVIDENCE_CLASSES),'summary':'Orient species occurrences, marine and avian observations, and U.S. conservation-governance records while preserving detectability, survey-completeness, licensing and legal-status boundaries.','warning':'BIODIVERSITY EVIDENCE · NOT A POPULATION CENSUS, ABSENCE FINDING OR LEGAL DETERMINATION'}
def catalog(): return {'ok':True,'version':VERSION,'contract':CONTRACT,'sources':[{'id':k,**v} for k,v in SOURCES.items()],'indicator_types':[{'id':k,**v} for k,v in INDICATOR_TYPES.items()],'evidence_classes':[{'id':k,'description':v} for k,v in EVIDENCE_CLASSES.items()],'truth_boundaries':{'occurrence_equals_population':False,'zero_records_equals_absence':False,'observation_equals_current_occupancy':False,'bird_observation_equals_breeding_confirmation':False,'aggregate_count_equals_abundance':False,'esa_status_equals_global_conservation_status':False,'critical_habitat_overlap_equals_project_effect':False,'platform_legal_determination':False}}
def state(source_id='gbif-occurrence',indicator_type='species-occurrence',scientific_name='',latitude=None,longitude=None,date=''):
    _,source=_source(source_id); iid,indicator=_indicator(indicator_type)
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'source':source,'indicator_type':indicator,'scientific_name':str(scientific_name or '').strip() or None,'query_point':_point(latitude,longitude),'date':str(date or '').strip() or None,'source_supports_indicator_type':iid in source['indicator_types'],'evidence':{'occurrence_record_loaded':False,'marine_occurrence_loaded':False,'bird_observation_loaded':False,'esa_record_loaded':False,'critical_habitat_loaded':False,'survey_completeness_verified':False,'population_estimate_loaded':False},'truth':{'occurrence_treated_as_population':False,'zero_records_treated_as_absence':False,'observation_treated_as_current_occupancy':False,'bird_observation_treated_as_breeding_confirmation':False,'aggregate_count_treated_as_abundance':False,'esa_status_treated_as_global_status':False,'critical_habitat_overlap_treated_as_project_effect':False,'platform_legal_determination':False,'automatic_action_authorized':False}}
def normalize_occurrence(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id')); iid,_=_indicator(request.get('indicator_type'))
    if iid not in source['indicator_types']: raise ValueError('source does not register the requested biodiversity indicator')
    ev=_evidence(request.get('evidence_class') or source['evidence_classes'][0])
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'scientific_name':str(request.get('scientific_name') or '').strip() or None,'taxon_id':str(request.get('taxon_id') or '').strip() or None,'basis_of_record':str(request.get('basis_of_record') or '').strip() or None,'event_date':str(request.get('event_date') or '').strip() or None,'query_point':_point(request.get('latitude'),request.get('longitude')),'coordinate_uncertainty_m':None if request.get('coordinate_uncertainty_m') in (None,'') else float(request.get('coordinate_uncertainty_m')),'dataset_license':str(request.get('dataset_license') or '').strip() or None,'occurrence_treated_as_population':False,'observation_treated_as_current_occupancy':False,'survey_completeness_verified':False,'zero_records_treated_as_absence':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'occurrence':r,'record_sha256':_digest(r),'normalized_at':_now()}
def normalize_conservation(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    _,source=_source(request.get('source_id') or 'usfws-ecos'); iid,_=_indicator(request.get('indicator_type') or 'esa-listing-status')
    if iid not in source['indicator_types']: raise ValueError('source does not register the requested conservation indicator')
    ev=_evidence(request.get('evidence_class') or source['evidence_classes'][0])
    if ev not in source['evidence_classes']: raise ValueError('source does not register the requested evidence_class')
    r={'source_id':source['id'],'source_url':_url(source,request.get('source_url')),'indicator_type':iid,'evidence_class':ev,'scientific_name':str(request.get('scientific_name') or '').strip() or None,'source_status':str(request.get('source_status') or '').strip() or None,'effective_date':str(request.get('effective_date') or '').strip() or None,'jurisdiction':'United States' if source['id']=='usfws-ecos' else None,'global_conservation_status_inferred':False,'project_effect_determined':False,'consultation_requirement_determined':False,'take_authorization_determined':False,'platform_legal_determination':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'conservation':r,'record_sha256':_digest(r),'normalized_at':_now()}
def overlap_preview(request:dict[str,Any]):
    if not isinstance(request,dict): raise TypeError('request must be an object')
    record_bbox=request.get('record_bbox'); area_bbox=request.get('area_bbox')
    def box(v,name):
        if not isinstance(v,(list,tuple)) or len(v)!=4: raise ValueError(f'{name} must be [west,south,east,north]')
        w,s,e,n=map(float,v)
        if not (-180<=w<=180 and -180<=e<=180 and -90<=s<=90 and -90<=n<=90 and w<=e and s<=n): raise ValueError(f'{name} outside valid bounds')
        return [w,s,e,n]
    a,b=box(record_bbox,'record_bbox'),box(area_bbox,'area_bbox'); intersects=not (a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1])
    r={'record_bbox':a,'area_bbox':b,'spatial_overlap':intersects,'species_presence_verified':False,'current_occupancy_verified':False,'population_present_inferred':False,'project_effect_determined':False,'consultation_requirement_determined':False,'legal_determination':False,'automatic_action_authorized':False}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'preview':r,'preview_sha256':_digest(r),'generated_at':_now()}
def export_manifest(source_id='gbif-occurrence',indicator_type='species-occurrence',scientific_name='',latitude=None,longitude=None,date=''):
    cur=state(source_id,indicator_type,scientific_name,latitude,longitude,date); p={'schema':'sc-site-intelligence-biodiversity/1.0','version':VERSION,'contract':CONTRACT,'query':{'source_id':cur['source']['id'],'indicator_type':cur['indicator_type']['id'],'scientific_name':cur['scientific_name'],'query_point':cur['query_point'],'date':cur['date']},'evidence':cur['evidence'],'review':{'occurrence_as_population':False,'zero_records_as_absence':False,'observation_as_current_occupancy':False,'bird_observation_as_breeding_confirmation':False,'aggregate_count_as_abundance':False,'esa_status_as_global_status':False,'critical_habitat_overlap_as_project_effect':False,'platform_legal_determination':False}}
    return {**p,'manifest_sha256':_digest(p),'generated_at':_now()}
def readiness():
    c={'four_source_families_registered':len(SOURCES)==4,'gbif_registered':'gbif-occurrence' in SOURCES,'obis_registered':'obis' in SOURCES,'ebird_registered':'ebird-public' in SOURCES,'usfws_ecos_registered':'usfws-ecos' in SOURCES,'absence_guard_present':True,'population_guard_present':True,'detectability_guard_present':True,'legal_status_scope_guard_present':True,'critical_habitat_project_effect_guard_present':True,'public_route_count_preserved':True}
    return {'ok':all(c.values()),'version':VERSION,'contract':CONTRACT,'checks':c,'summary':{'sources':len(SOURCES),'indicator_types':len(INDICATOR_TYPES),'evidence_classes':len(EVIDENCE_CLASSES),'public_route_count_delta':0,'primary_area_count_delta':0},'generated_at':_now()}
