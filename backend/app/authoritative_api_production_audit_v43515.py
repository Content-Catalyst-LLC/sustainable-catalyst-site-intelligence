from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
from typing import Any
from .version import APP_VERSION
from . import authoritative_api_audit_v43515 as prior
from .authoritative_connectors_v43515 import connector_readiness
from .evidence_intelligence_v4357 import readiness as evidence_readiness
from .workspace_evidence_unification_v4358 import readiness as workspace_evidence_readiness
VERSION=APP_VERSION; CONTRACT='authoritative-api-coverage-production-audit-v43515'
def _now(): return datetime.now(timezone.utc).isoformat()
def _pct(n,d): return round(100*n/d,2) if d else 0.0
def closure_ledger(settings:Any=None):
    rows=prior.source_inventory(settings); matrix=prior.workspace_matrix(settings)['workspaces']; gaps=[]
    for r in rows:
        if r.get('machine_readable') and r.get('access_class') in {'REGISTERED','AUTH_REQUIRED','BULK','STALE'}:
            gaps.append({k:r.get(k) for k in ('workspace','source_id','title','organization','host','protocol','access_class','configuration_key','implementation_evidence','limitations')})
    gaps.sort(key=lambda x:(x['access_class'],str(x['workspace']),str(x['source_id']))); c=Counter(x['access_class'] for x in gaps); lookup={x['workspace']:x for x in matrix}
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'summary':{'machine_readable_gap_records':len(gaps),'registered_not_retrieved':c['REGISTERED'],'configuration_required':c['AUTH_REQUIRED'],'bulk_only':c['BULK'],'stale':c['STALE'],'mining_registered_backlog':lookup['Mining & Critical Materials']['registered_backlog'],'industrial_registered_backlog':lookup['Industrial Manufacturing & Trade']['registered_backlog']},'workspace_ledger':matrix,'gap_records':gaps,'generated_at':_now()}
def production_audit(settings=None):
    base=prior.audit_overview(settings); rows=[r for r in prior.source_inventory(settings) if r.get('machine_readable')]; c=Counter(r['access_class'] for r in rows); ledger=closure_ledger(settings); cl=prior.closure_status(settings)
    checks={'source_inventory_reconciles':sum(c.values())==len(rows),'connector_catalog_ready':connector_readiness(settings)['ok'],'metric_semantics_and_precedence_ready':evidence_readiness()['ok'],'workspace_truth_unification_ready':workspace_evidence_readiness()['ok'],'no_known_stale_implemented_connectors':c['STALE']==0,'mining_registered_backlog_closed':cl['workspaces']['mining_critical_materials']['registered_backlog']==0,'industrial_registered_backlog_closed':cl['workspaces']['industrial_manufacturing_trade']['registered_backlog']==0,'external_source_health_not_used_as_release_blocker':True}
    ready=all(checks.values()); active=c['LIVE']+c['DISCOVERY']; gated=active+c['AUTH_REQUIRED']
    return {'ok':ready,'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'production_controls_ready':ready,'coverage_closure_complete':c['REGISTERED']==0,'closure_status':'high-priority-workspaces-closure-v-complete-backlog-open' if ready and c['REGISTERED'] else 'complete' if ready else 'blocked','summary':base['summary'],'machine_readable_summary':{'registrations':len(rows),'counts':{k:int(c.get(k,0)) for k in prior.ACCESS_CLASSES},'implemented_discovery_or_configuration_gated':gated,'registered_not_retrieved':c['REGISTERED']},'coverage':{'live_or_discovery_pct_of_machine_readable':_pct(active,len(rows)),'implemented_discovery_or_configuration_gated_pct_of_machine_readable':_pct(gated,len(rows)),'registered_not_retrieved_pct_of_machine_readable':_pct(c['REGISTERED'],len(rows))},'checks':checks,'closure_v':cl,'closure_ledger_summary':ledger['summary'],'next_connector_targets':list(base.get('priority_connector_targets') or []),'generated_at':_now()}
def production_readiness(settings=None):
    a=production_audit(settings); return {'ok':a['production_controls_ready'],'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'coverage_closure_complete':a['coverage_closure_complete'],'closure_status':a['closure_status'],'checks':a['checks'],'summary':a['closure_ledger_summary'],'generated_at':_now()}
def audit_overview(settings=None):
    p=prior.audit_overview(settings); p['production_audit']=production_audit(settings); p['closure_ledger']=closure_ledger(settings)['summary']; return p
def audit_catalog(settings=None,workspace='',access_class='',query=''): return prior.audit_catalog(settings,workspace,access_class,query)
def workspace_matrix(settings=None): return prior.workspace_matrix(settings)
def audit_readiness(settings=None):
    p=prior.audit_readiness(settings); p['checks']['production_audit_ready']=production_readiness(settings)['ok']; p['ok']=all(p['checks'].values()); return p
