from __future__ import annotations
from typing import Any
from .version import APP_VERSION
from . import authoritative_api_audit_v43515 as prior
from .credential_configuration_v43516 import canonical_configuration_for_source, credential_registry

VERSION=APP_VERSION
CONTRACT=prior.CONTRACT
AUDIT_DATE='2026-08-11'
ACCESS_CLASSES=prior.ACCESS_CLASSES
COMPLETED_CONNECTOR_TARGETS=prior.COMPLETED_CONNECTOR_TARGETS
PRIORITY_CONNECTOR_TARGETS=prior.PRIORITY_CONNECTOR_TARGETS

def source_inventory(settings:Any=None):
    rows=[dict(x) for x in prior.source_inventory(settings)]
    for row in rows:
        if row.get('machine_readable') and row.get('access_class')=='AUTH_REQUIRED':
            cfg=canonical_configuration_for_source(str(row.get('workspace') or ''),str(row.get('source_id') or ''),settings)
            if cfg: row.update(cfg)
    return rows

def workspace_matrix(settings=None):
    # Reuse prior aggregation over canonicalized rows by reproducing its compact logic.
    from collections import defaultdict
    groups=defaultdict(list)
    for r in source_inventory(settings): groups[r['workspace']].append(r)
    out=[]
    for name,rows in sorted(groups.items()):
        c=prior._counts(rows); machine=sum(bool(r.get('machine_readable')) for r in rows); machine_registered=sum(1 for r in rows if r.get('machine_readable') and r.get('access_class')=='REGISTERED')
        out.append({'workspace':name,'source_registrations':len(rows),'machine_readable_registrations':machine,'counts':c,'registered_backlog':machine_registered,'fully_live':machine>0 and machine_registered==0 and c['STALE']==0 and c['AUTH_REQUIRED']==0,'connector_gap':machine_registered+c['BULK']+c['AUTH_REQUIRED']+c['STALE']})
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'workspace_count':len(out),'workspaces':out,'generated_at':prior._now()}

def closure_status(settings=None): return prior.closure_status(settings)

def audit_overview(settings=None):
    p=prior.audit_overview(settings)
    p['version']=VERSION
    p['credential_configuration']=credential_registry(settings)
    p['principles']=list(p.get('principles') or [])+['All AUTH_REQUIRED machine registrations resolve through one canonical credential profile registry.','Credential diagnostics never return, mask, hash, fingerprint, or probe secret material.']
    return p

def audit_catalog(settings=None,workspace='',access_class='',query=''):
    rows=source_inventory(settings); w=(workspace or '').lower(); a=(access_class or '').upper(); q=(query or '').lower()
    if a and a not in ACCESS_CLASSES: raise ValueError('invalid access_class')
    if w: rows=[r for r in rows if w in r['workspace'].lower() or w==r['module'].lower()]
    if a: rows=[r for r in rows if r['access_class']==a]
    if q: rows=[r for r in rows if q in ' '.join(str(r.get(k) or '') for k in ('title','organization','host','source_id','protocol','workspace')).lower()]
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'count':len(rows),'counts':prior._counts(rows),'access_classes':list(ACCESS_CLASSES),'sources':rows,'generated_at':prior._now()}

def audit_readiness(settings=None):
    p=prior.audit_readiness(settings); p['version']=VERSION; p['checks']['canonical_credential_registry_present']=credential_registry(settings)['mapped_auth_required_registrations']==17; p['ok']=all(p['checks'].values()); return p
