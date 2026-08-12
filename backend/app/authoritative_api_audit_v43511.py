from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib,json
from typing import Any
from .version import APP_VERSION
from . import authoritative_api_audit_v43510 as prior

VERSION=APP_VERSION; CONTRACT=prior.CONTRACT; AUDIT_DATE='2026-08-11'; ACCESS_CLASSES=prior.ACCESS_CLASSES
COMPLETED_CONNECTOR_TARGETS=tuple(prior.COMPLETED_CONNECTOR_TARGETS)+(
 {'id':'osm-power-overpass','workspace':'Energy Infrastructure & Power Systems','state':'LIVE','completed_in':'4.35.20'},
 {'id':'ember-electricity-data','workspace':'Energy Infrastructure & Power Systems','state':'AUTH_REQUIRED','completed_in':'4.35.20'},
 {'id':'entsoe-transparency','workspace':'Energy Infrastructure & Power Systems','state':'AUTH_REQUIRED','completed_in':'4.35.20'},
 {'id':'openstreetmap-telecom','workspace':'Digital Connectivity','state':'LIVE','completed_in':'4.35.20'},
 {'id':'mlab-network-performance','workspace':'Digital Connectivity','state':'DISCOVERY','completed_in':'4.35.20'},
 {'id':'fcc-broadband-data','workspace':'Digital Connectivity','state':'DISCOVERY','completed_in':'4.35.20'},
)
PRIORITY_CONNECTOR_TARGETS=tuple(x for x in prior.PRIORITY_CONNECTOR_TARGETS if x.get('id')!='measurement-lab')

def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def _configured(settings,name): return bool(str(getattr(settings,name,'') or '').strip()) if settings is not None else False

def source_inventory(settings:Any=None):
    rows=[dict(x) for x in prior.source_inventory(settings)]
    for r in rows:
        sid=r.get('source_id'); ws=r.get('workspace')
        if ws=='Energy Infrastructure & Power Systems':
            if sid=='openstreetmap-power':
                r.update(access_class='LIVE',implementation_evidence='authoritative_connectors_v43511 bounded Overpass power retrieval',configuration_state='configured')
            elif sid=='eia-open-data':
                r.update(access_class='AUTH_REQUIRED',implementation_evidence='authoritative_connectors_v43511 EIA API v2 bounded electricity retrieval',configuration_key='SC_SI_EIA_API_KEY',configuration_state='configured' if _configured(settings,'eia_api_key') else 'configuration-required')
            elif sid=='ember-electricity-data':
                r.update(access_class='AUTH_REQUIRED',implementation_evidence='authoritative_connectors_v43511 Ember API v1 bounded electricity retrieval',configuration_key='SC_SI_EMBER_API_KEY',configuration_state='configured' if _configured(settings,'ember_api_key') else 'configuration-required')
            elif sid=='entsoe-transparency':
                r.update(access_class='AUTH_REQUIRED',implementation_evidence='authoritative_connectors_v43511 ENTSO-E web API bounded XML retrieval',configuration_key='SC_SI_ENTSOE_SECURITY_TOKEN',configuration_state='configured' if _configured(settings,'entsoe_security_token') else 'configuration-required')
        elif ws=='Digital Connectivity':
            if sid=='openstreetmap-telecom':
                r.update(access_class='LIVE',implementation_evidence='authoritative_connectors_v43511 bounded Overpass telecom retrieval',configuration_state='configured')
            elif sid=='mlab-network-performance':
                r.update(access_class='DISCOVERY',implementation_evidence='authoritative_connectors_v43511 M-Lab Locate API v2 service discovery; historical performance remains BigQuery-backed',configuration_state='configured')
            elif sid=='fcc-broadband-data':
                r.update(access_class='DISCOVERY',implementation_evidence='authoritative_connectors_v43511 FCC BDC Public Data API release-vintage discovery',configuration_state='configured')
    return rows

def _counts(rows):
    c=Counter(r['access_class'] for r in rows); return {k:int(c.get(k,0)) for k in ACCESS_CLASSES}
def _unique(r): return f"host:{r.get('host')}" if r.get('host') else f"record:{r.get('module')}:{r.get('source_id')}"

def workspace_matrix(settings=None):
    groups=defaultdict(list)
    for r in source_inventory(settings): groups[r['workspace']].append(r)
    out=[]
    for name,rows in sorted(groups.items()):
        c=_counts(rows); machine=sum(bool(r.get('machine_readable')) for r in rows)
        out.append({'workspace':name,'source_registrations':len(rows),'machine_readable_registrations':machine,'counts':c,'registered_backlog':c['REGISTERED'],'fully_live':machine>0 and c['REGISTERED']==0 and c['STALE']==0 and c['AUTH_REQUIRED']==0,'connector_gap':c['REGISTERED']+c['BULK']+c['AUTH_REQUIRED']+c['STALE']})
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'workspace_count':len(out),'workspaces':out,'generated_at':_now()}

def closure_status(settings=None):
    rows={r['workspace']:r for r in workspace_matrix(settings)['workspaces']}
    energy=rows['Energy Infrastructure & Power Systems']; digital=rows['Digital Connectivity']
    return {'ok':energy['registered_backlog']==0 and digital['registered_backlog']==0,'version':VERSION,'contract':'workspace-connector-closure-i','network_calls_performed':False,'workspaces':{'energy':energy,'digital':digital},'energy_operational_without_credentials':energy['counts']['LIVE']>0,'energy_official_api_credentials_remaining':energy['counts']['AUTH_REQUIRED'],'digital_operational_without_credentials':digital['counts']['LIVE']+digital['counts']['DISCOVERY']>0 and digital['counts']['AUTH_REQUIRED']==0,'generated_at':_now()}

def audit_overview(settings=None):
    rows=source_inventory(settings); c=_counts(rows); machine=[r for r in rows if r.get('machine_readable')]
    base=prior.audit_overview(settings)
    payload={'ok':True,'version':VERSION,'contract':CONTRACT,'audit_date':AUDIT_DATE,'classification':base['classification'],'summary':{'source_registrations':len(rows),'unique_source_endpoints_or_records':len({_unique(r) for r in rows}),'workspaces_with_source_registries':len({r['workspace'] for r in rows}),'machine_readable_registrations':len(machine),'implemented_or_configuration_gated_registrations':c['LIVE']+c['DISCOVERY']+c['AUTH_REQUIRED'],'counts':c,'registered_but_not_retrieved':c['REGISTERED'],'stale_implemented_connectors':c['STALE']},'principles':list(base.get('principles') or [])+['Energy and Digital now have zero REGISTERED machine-interface backlog; credential-gated official energy APIs remain explicit configuration work.','M-Lab Locate and FCC BDC release discovery are DISCOVERY, not performance/availability observations.','OSM infrastructure retrieval is supplemental community mapping evidence, not an authoritative operational determination.'],'verified_machine_interfaces':list(base.get('verified_machine_interfaces') or []),'completed_connector_targets':list(COMPLETED_CONNECTOR_TARGETS),'priority_connector_targets':list(PRIORITY_CONNECTOR_TARGETS),'closure_i':closure_status(settings),'generated_at':_now()}
    payload['audit_sha256']=_digest({'summary':payload['summary'],'closure_i':payload['closure_i']}); return payload

def audit_catalog(settings=None,workspace='',access_class='',query=''):
    rows=source_inventory(settings); w=(workspace or '').lower(); a=(access_class or '').upper(); q=(query or '').lower()
    if a and a not in ACCESS_CLASSES: raise ValueError('invalid access_class')
    if w: rows=[r for r in rows if w in r['workspace'].lower() or w==r['module'].lower()]
    if a: rows=[r for r in rows if r['access_class']==a]
    if q: rows=[r for r in rows if q in ' '.join(str(r.get(k) or '') for k in ('title','organization','host','source_id','protocol','workspace')).lower()]
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'count':len(rows),'counts':_counts(rows),'access_classes':list(ACCESS_CLASSES),'sources':rows,'generated_at':_now()}

def audit_readiness(settings=None):
    o=audit_overview(settings); cl=closure_status(settings)
    checks={'inventory_present':o['summary']['source_registrations']>=188,'zero_stale':o['summary']['counts']['STALE']==0,'energy_registered_backlog_zero':cl['workspaces']['energy']['registered_backlog']==0,'digital_registered_backlog_zero':cl['workspaces']['digital']['registered_backlog']==0,'network_free':True}
    return {'ok':all(checks.values()),'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'checks':checks,'closure_i':cl,'generated_at':_now()}
