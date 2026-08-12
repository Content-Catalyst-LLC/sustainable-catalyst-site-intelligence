from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib,json
from typing import Any
from .version import APP_VERSION
from . import authoritative_api_audit_v43514 as prior

VERSION=APP_VERSION; CONTRACT=prior.CONTRACT; AUDIT_DATE='2026-08-11'; ACCESS_CLASSES=prior.ACCESS_CLASSES
COMPLETED_CONNECTOR_TARGETS=tuple(prior.COMPLETED_CONNECTOR_TARGETS)+(
 {'id':'osm-mining-overpass','workspace':'Mining & Critical Materials','state':'LIVE','completed_in':'4.35.22'},
 {'id':'usgs-usmin-sdc','workspace':'Mining & Critical Materials','state':'DISCOVERY','completed_in':'4.35.22'},
 {'id':'usgs-mcs-2026-sdc','workspace':'Mining & Critical Materials','state':'DISCOVERY','completed_in':'4.35.22'},
 {'id':'osm-industrial-overpass','workspace':'Industrial Manufacturing & Trade','state':'LIVE','completed_in':'4.35.22'},
 {'id':'world-bank-wits-trade-stats','workspace':'Industrial Manufacturing & Trade','state':'LIVE','completed_in':'4.35.22'},
)
PRIORITY_CONNECTOR_TARGETS=tuple(x for x in prior.PRIORITY_CONNECTOR_TARGETS if x.get('id') not in {'openstreetmap-mining','usgs-usmin','usgs-mcs-2026','openstreetmap-industrial','world-bank-wits-trade'})
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def _counts(rows):
    c=Counter(r['access_class'] for r in rows); return {k:int(c.get(k,0)) for k in ACCESS_CLASSES}
def _unique(r): return f"host:{r.get('host')}" if r.get('host') else f"record:{r.get('module')}:{r.get('source_id')}"

def source_inventory(settings:Any=None):
    rows=[dict(x) for x in prior.source_inventory(settings)]
    for r in rows:
        ws=r.get('workspace'); sid=r.get('source_id')
        if ws=='Mining & Critical Materials' and sid=='openstreetmap-mining':
            r.update(access_class='LIVE',implementation_evidence='authoritative_connectors_v43515 bounded OSM mining/quarry Overpass retrieval',configuration_state='configured',authentication='public')
        elif ws=='Mining & Critical Materials' and sid=='usgs-usmin':
            r.update(access_class='DISCOVERY',protocol='USGS Science Data Catalog REST / JSON',api_url='https://data.usgs.gov/datacatalog/api/search/USGS%3A6464de5bd34ec179a83d9e6c',implementation_evidence='authoritative_connectors_v43515 USGS SDC metadata discovery',configuration_state='configured',authentication='public')
        elif ws=='Mining & Critical Materials' and sid=='usgs-mcs-2026':
            r.update(access_class='DISCOVERY',protocol='USGS Science Data Catalog REST / JSON',api_url='https://data.usgs.gov/datacatalog/api/search/USGS%3A69837e43b66b01367d7ec7c7',implementation_evidence='authoritative_connectors_v43515 MCS 2026 SDC data-release discovery',configuration_state='configured',authentication='public')
        elif ws=='Industrial Manufacturing & Trade' and sid=='openstreetmap-industrial':
            r.update(access_class='LIVE',implementation_evidence='authoritative_connectors_v43515 bounded OSM industrial Overpass retrieval',configuration_state='configured',authentication='public')
        elif ws=='Industrial Manufacturing & Trade' and sid=='world-bank-wits-trade':
            r.update(access_class='LIVE',protocol='REST / JSON / SDMX',implementation_evidence='authoritative_connectors_v43515 bounded WITS Trade Stats retrieval',configuration_state='configured',authentication='public')
    return rows

def workspace_matrix(settings=None):
    groups=defaultdict(list)
    for r in source_inventory(settings): groups[r['workspace']].append(r)
    out=[]
    for name,rows in sorted(groups.items()):
        c=_counts(rows); machine=sum(bool(r.get('machine_readable')) for r in rows); machine_registered=sum(1 for r in rows if r.get('machine_readable') and r.get('access_class')=='REGISTERED')
        out.append({'workspace':name,'source_registrations':len(rows),'machine_readable_registrations':machine,'counts':c,'registered_backlog':machine_registered,'fully_live':machine>0 and machine_registered==0 and c['STALE']==0 and c['AUTH_REQUIRED']==0,'connector_gap':machine_registered+c['BULK']+c['AUTH_REQUIRED']+c['STALE']})
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'workspace_count':len(out),'workspaces':out,'generated_at':_now()}
def closure_status(settings=None):
    rows={r['workspace']:r for r in workspace_matrix(settings)['workspaces']}; mi=rows['Mining & Critical Materials']; ind=rows['Industrial Manufacturing & Trade']
    return {'ok':mi['registered_backlog']==0 and ind['registered_backlog']==0,'version':VERSION,'contract':'workspace-connector-closure-v','network_calls_performed':False,'workspaces':{'mining_critical_materials':mi,'industrial_manufacturing_trade':ind},'mining_live_without_credentials':mi['counts']['LIVE']>0,'industrial_live_without_credentials':ind['counts']['LIVE']>0,'generated_at':_now()}
def audit_overview(settings=None):
    rows=source_inventory(settings); machine=[r for r in rows if r.get('machine_readable')]; base=prior.audit_overview(settings)
    payload={'ok':True,'version':VERSION,'contract':CONTRACT,'audit_date':AUDIT_DATE,'classification':base['classification'],'summary':{'source_registrations':len(rows),'unique_source_endpoints_or_records':len({_unique(r) for r in rows}),'workspaces_with_source_registries':len({r['workspace'] for r in rows}),'machine_readable_registrations':len(machine),'implemented_or_configuration_gated_registrations':sum(1 for r in machine if r['access_class'] in {'LIVE','DISCOVERY','AUTH_REQUIRED'}),'counts':_counts(machine),'registered_but_not_retrieved':sum(1 for r in machine if r['access_class']=='REGISTERED'),'stale_implemented_connectors':sum(1 for r in machine if r['access_class']=='STALE')},'principles':list(base.get('principles') or [])+['Mining/Critical Materials and Industrial Manufacturing/Trade now have zero REGISTERED machine-interface backlog.','USGS SDC metadata discovery remains distinct from mine operations and annual commodity statistics.','WITS trade data remain statistical records rather than physical shipment telemetry.'],'verified_machine_interfaces':list(base.get('verified_machine_interfaces') or []),'completed_connector_targets':list(COMPLETED_CONNECTOR_TARGETS),'priority_connector_targets':list(PRIORITY_CONNECTOR_TARGETS),'closure_v':closure_status(settings),'generated_at':_now()}
    payload['audit_sha256']=_digest({'summary':payload['summary'],'closure_v':payload['closure_v']}); return payload
def audit_catalog(settings=None,workspace='',access_class='',query=''):
    rows=source_inventory(settings); w=(workspace or '').lower(); a=(access_class or '').upper(); q=(query or '').lower()
    if a and a not in ACCESS_CLASSES: raise ValueError('invalid access_class')
    if w: rows=[r for r in rows if w in r['workspace'].lower() or w==r['module'].lower()]
    if a: rows=[r for r in rows if r['access_class']==a]
    if q: rows=[r for r in rows if q in ' '.join(str(r.get(k) or '') for k in ('title','organization','host','source_id','protocol','workspace')).lower()]
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'count':len(rows),'counts':_counts(rows),'access_classes':list(ACCESS_CLASSES),'sources':rows,'generated_at':_now()}
def audit_readiness(settings=None):
    o=audit_overview(settings); cl=closure_status(settings)
    checks={'inventory_present':o['summary']['source_registrations']>=191,'zero_stale':o['summary']['counts']['STALE']==0,'mining_registered_backlog_zero':cl['workspaces']['mining_critical_materials']['registered_backlog']==0,'industrial_registered_backlog_zero':cl['workspaces']['industrial_manufacturing_trade']['registered_backlog']==0,'network_free':True}
    return {'ok':all(checks.values()),'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'checks':checks,'closure_v':cl,'generated_at':_now()}
