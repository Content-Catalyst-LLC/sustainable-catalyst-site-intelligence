from __future__ import annotations
from collections import Counter
from .version import APP_VERSION
from . import authoritative_api_production_audit_v43515 as prior_prod
from . import authoritative_api_audit_v43516 as audit
from .credential_configuration_v43516 import credential_readiness, credential_registry

VERSION=APP_VERSION
CONTRACT='authoritative-api-coverage-production-audit-v43516'

def closure_ledger(settings=None):
    p=prior_prod.closure_ledger(settings); p['version']=VERSION
    # Replace gap records with canonical v4.35.16 configuration metadata.
    rows=audit.source_inventory(settings); gaps=[]
    for r in rows:
        if r.get('machine_readable') and r.get('access_class') in {'REGISTERED','AUTH_REQUIRED','BULK','STALE'}:
            gaps.append({k:r.get(k) for k in ('workspace','source_id','title','organization','host','protocol','access_class','configuration_key','configuration_state','credential_profile','implementation_evidence','limitations')})
    gaps.sort(key=lambda x:(x['access_class'],str(x['workspace']),str(x['source_id'])))
    p['gap_records']=gaps; return p

def production_audit(settings=None):
    p=prior_prod.production_audit(settings); p['version']=VERSION; p['contract']=CONTRACT
    cred=credential_registry(settings); ready=credential_readiness(settings)
    p['credential_configuration']={
        'control_plane_ready':ready['ok'],
        'configuration_complete':cred['configuration_complete'],
        'completion_status':cred['completion_status'],
        'profile_count':cred['profile_count'],
        'mapped_auth_required_registrations':cred['mapped_auth_required_registrations'],
        'states':cred['states'],
        'release_blocking':False,
    }
    p['checks']['credential_control_plane_ready']=ready['ok']
    p['production_controls_ready']=all(p['checks'].values()); p['ok']=p['production_controls_ready']
    return p

def production_readiness(settings=None):
    a=production_audit(settings)
    return {'ok':a['production_controls_ready'],'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'coverage_closure_complete':a['coverage_closure_complete'],'closure_status':a['closure_status'],'checks':a['checks'],'summary':a['closure_ledger_summary'],'credential_configuration':a['credential_configuration'],'generated_at':prior_prod._now()}

def audit_overview(settings=None):
    p=audit.audit_overview(settings); p['production_audit']=production_audit(settings); p['closure_ledger']=closure_ledger(settings)['summary']; return p

def audit_catalog(settings=None,workspace='',access_class='',query=''): return audit.audit_catalog(settings,workspace,access_class,query)
def workspace_matrix(settings=None): return audit.workspace_matrix(settings)
def audit_readiness(settings=None):
    p=audit.audit_readiness(settings); p['checks']['production_audit_ready']=production_readiness(settings)['ok']; p['ok']=all(p['checks'].values()); return p
