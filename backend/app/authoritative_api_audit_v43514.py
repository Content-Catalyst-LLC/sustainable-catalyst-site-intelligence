from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib,json
from typing import Any
from .version import APP_VERSION
from . import authoritative_api_audit_v43513 as prior

VERSION=APP_VERSION; CONTRACT=prior.CONTRACT; AUDIT_DATE='2026-08-11'; ACCESS_CLASSES=prior.ACCESS_CLASSES
COMPLETED_CONNECTOR_TARGETS=tuple(prior.COMPLETED_CONNECTOR_TARGETS)+(
 {'id':'gdacs-events-v1','workspace':'Humanitarian Intelligence','state':'LIVE','completed_in':'4.35.16'},
 {'id':'hdx-ckan-discovery','workspace':'Conflict & Human Security','state':'DISCOVERY','completed_in':'4.35.16'},
 {'id':'hdx-hapi-food-security','workspace':'Humanitarian Intelligence','state':'AUTH_REQUIRED','completed_in':'4.35.16'},
 {'id':'ipc-food-security-api','workspace':'Agriculture, Crops & Food Systems','state':'AUTH_REQUIRED','completed_in':'4.35.16'},
 {'id':'fews-net-data-platform','workspace':'Agriculture, Crops & Food Systems','state':'LIVE','completed_in':'4.35.16'},
)
PRIORITY_CONNECTOR_TARGETS=tuple(x for x in prior.PRIORITY_CONNECTOR_TARGETS if x.get('id') not in {'gdacs','hdx','ipc-food-security-api','fews-net-data-platform'})
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def _configured(settings,name): return bool(str(getattr(settings,name,'') or '').strip()) if settings is not None else False

def _new_row(*,workspace,module,source_id,title,organization,host,api_url,protocol,access_class,configuration_key=None,authentication='public',coverage='',limitations=''):
    return {'workspace':workspace,'module':module,'registry':'connector-closure-iv','source_id':source_id,'title':title,'organization':organization,'authority':'official-intergovernmental-or-public-institution','host':host,'url':api_url,'api_url':api_url,'documentation_url':None,'protocol':protocol,'machine_readable':True,'access_class':access_class,'implementation_evidence':'authoritative_connectors_v43514 implemented bounded retrieval/discovery','configuration_state':'configuration-required' if access_class=='AUTH_REQUIRED' else 'configured','configuration_key':configuration_key,'authentication':authentication,'coverage':coverage or workspace,'limitations':limitations}

def source_inventory(settings:Any=None):
    rows=[dict(x) for x in prior.source_inventory(settings)]
    for r in rows:
        sid=r.get('source_id'); ws=r.get('workspace')
        if ws=='Humanitarian Intelligence' and sid=='gdacs':
            r.update(access_class='LIVE',api_url='https://www.gdacs.org/gdacsapi/api/Events/geteventlist/latest',implementation_evidence='authoritative_connectors_v43514 bounded GDACS Events API retrieval',configuration_state='configured',configuration_key=None,authentication='public')
        elif ws=='Sources & Methodology' and sid=='reliefweb':
            r.update(access_class='AUTH_REQUIRED',api_url='https://api.reliefweb.int/v2/reports',implementation_evidence='unified_live_events ReliefWeb V2 retrieval; approved appname required',configuration_key='SC_SI_RELIEFWEB_APPNAME',configuration_state='configured' if _configured(settings,'reliefweb_appname') else 'configuration-required',authentication='pre-approved appname')
        elif ws=='Conflict & Human Security' and sid=='hdx':
            r.update(machine_readable=True,access_class='DISCOVERY',protocol='CKAN REST / JSON',api_url='https://data.humdata.org/api/action/package_search',implementation_evidence='authoritative_connectors_v43514 bounded HDX CKAN dataset discovery',configuration_state='configured',configuration_key=None,authentication='public metadata discovery; some tabular resources require token')
    ids={(r.get('workspace'),r.get('source_id')) for r in rows}
    additions=[
      _new_row(workspace='Humanitarian Intelligence',module='authoritative_connectors_v43514',source_id='hdx-hapi-food-security',title='HDX HAPI Food Security',organization='OCHA Centre for Humanitarian Data',host='hapi.humdata.org',api_url='https://hapi.humdata.org/api/v2/food-security-nutrition-poverty/food-security',protocol='REST / JSON',access_class='AUTH_REQUIRED',configuration_key='SC_SI_HDX_HAPI_APP_IDENTIFIER',authentication='app_identifier',limitations='HAPI standardizes upstream data and may p-code provider geography; warnings, reference periods and original resource identifiers must remain visible.'),
      _new_row(workspace='Agriculture, Crops & Food Systems',module='authoritative_connectors_v43514',source_id='ipc-food-security-api',title='IPC-CH Public API',organization='Integrated Food Security Phase Classification',host='api.ipcinfo.org',api_url='https://api.ipcinfo.org/analysis',protocol='REST / JSON / CSV / GeoJSON',access_class='AUTH_REQUIRED',configuration_key='SC_SI_IPC_API_KEY',authentication='API key',limitations='IPC classifications are analysis outputs for defined periods/geographies; Site Intelligence does not create or modify phases.'),
      _new_row(workspace='Agriculture, Crops & Food Systems',module='authoritative_connectors_v43514',source_id='fews-net-data-platform',title='FEWS NET Data Warehouse REST API',organization='Famine Early Warning Systems Network',host='fdw.fews.net',api_url='https://fdw.fews.net/api',protocol='REST / JSON / CSV / GeoJSON',access_class='LIVE',authentication='public data without authentication; account token optional for permissioned data',limitations='FEWS NET projections and classifications retain scenario/collection date and are not silently relabeled as IPC-issued classifications.'),
    ]
    for r in additions:
        if (r['workspace'],r['source_id']) not in ids:
            if r['source_id']=='hdx-hapi-food-security': r['configuration_state']='configured' if _configured(settings,'hdx_hapi_app_identifier') else 'configuration-required'
            if r['source_id']=='ipc-food-security-api': r['configuration_state']='configured' if _configured(settings,'ipc_api_key') else 'configuration-required'
            rows.append(r)
    return rows

def _counts(rows):
    c=Counter(r['access_class'] for r in rows); return {k:int(c.get(k,0)) for k in ACCESS_CLASSES}
def _unique(r): return f"host:{r.get('host')}" if r.get('host') else f"record:{r.get('module')}:{r.get('source_id')}"
def workspace_matrix(settings=None):
    groups=defaultdict(list)
    for r in source_inventory(settings): groups[r['workspace']].append(r)
    out=[]
    for name,rows in sorted(groups.items()):
        c=_counts(rows); machine=sum(bool(r.get('machine_readable')) for r in rows); machine_registered=sum(1 for r in rows if r.get('machine_readable') and r.get('access_class')=='REGISTERED')
        out.append({'workspace':name,'source_registrations':len(rows),'machine_readable_registrations':machine,'counts':c,'registered_backlog':machine_registered,'fully_live':machine>0 and machine_registered==0 and c['STALE']==0 and c['AUTH_REQUIRED']==0,'connector_gap':machine_registered+c['BULK']+c['AUTH_REQUIRED']+c['STALE']})
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'workspace_count':len(out),'workspaces':out,'generated_at':_now()}
def closure_status(settings=None):
    rows={r['workspace']:r for r in workspace_matrix(settings)['workspaces']}; ag=rows['Agriculture, Crops & Food Systems']; hu=rows['Humanitarian Intelligence']
    return {'ok':ag['registered_backlog']==0 and hu['registered_backlog']==0,'version':VERSION,'contract':'workspace-connector-closure-iv','network_calls_performed':False,'workspaces':{'agriculture_food_security':ag,'humanitarian':hu},'agriculture_live_without_credentials':ag['counts']['LIVE']>0,'humanitarian_live_without_credentials':hu['counts']['LIVE']>0,'generated_at':_now()}
def audit_overview(settings=None):
    rows=source_inventory(settings); c=_counts(rows); machine=[r for r in rows if r.get('machine_readable')]; base=prior.audit_overview(settings)
    payload={'ok':True,'version':VERSION,'contract':CONTRACT,'audit_date':AUDIT_DATE,'classification':base['classification'],'summary':{'source_registrations':len(rows),'unique_source_endpoints_or_records':len({_unique(r) for r in rows}),'workspaces_with_source_registries':len({r['workspace'] for r in rows}),'machine_readable_registrations':len(machine),'implemented_or_configuration_gated_registrations':sum(1 for r in machine if r['access_class'] in {'LIVE','DISCOVERY','AUTH_REQUIRED'}),'counts':_counts(machine),'registered_but_not_retrieved':sum(1 for r in machine if r['access_class']=='REGISTERED'),'stale_implemented_connectors':sum(1 for r in machine if r['access_class']=='STALE')},'principles':list(base.get('principles') or [])+['Agriculture/Food Security and Humanitarian Intelligence now have zero REGISTERED machine-interface backlog.','GDACS operational disaster alerts remain distinct from humanitarian needs assessments and national emergency instructions.','FEWS NET, IPC and HDX HAPI retain their own classification/scenario/reference-period semantics; Site Intelligence does not blend them into a synthetic food-security phase.'],'verified_machine_interfaces':list(base.get('verified_machine_interfaces') or []),'completed_connector_targets':list(COMPLETED_CONNECTOR_TARGETS),'priority_connector_targets':list(PRIORITY_CONNECTOR_TARGETS),'closure_iv':closure_status(settings),'generated_at':_now()}
    payload['audit_sha256']=_digest({'summary':payload['summary'],'closure_iv':payload['closure_iv']}); return payload
def audit_catalog(settings=None,workspace='',access_class='',query=''):
    rows=source_inventory(settings); w=(workspace or '').lower(); a=(access_class or '').upper(); q=(query or '').lower()
    if a and a not in ACCESS_CLASSES: raise ValueError('invalid access_class')
    if w: rows=[r for r in rows if w in r['workspace'].lower() or w==r['module'].lower()]
    if a: rows=[r for r in rows if r['access_class']==a]
    if q: rows=[r for r in rows if q in ' '.join(str(r.get(k) or '') for k in ('title','organization','host','source_id','protocol','workspace')).lower()]
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'count':len(rows),'counts':_counts(rows),'access_classes':list(ACCESS_CLASSES),'sources':rows,'generated_at':_now()}
def audit_readiness(settings=None):
    o=audit_overview(settings); cl=closure_status(settings)
    checks={'inventory_present':o['summary']['source_registrations']>=191,'zero_stale':o['summary']['counts']['STALE']==0,'agriculture_registered_backlog_zero':cl['workspaces']['agriculture_food_security']['registered_backlog']==0,'humanitarian_registered_backlog_zero':cl['workspaces']['humanitarian']['registered_backlog']==0,'network_free':True}
    return {'ok':all(checks.values()),'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'checks':checks,'closure_iv':cl,'generated_at':_now()}
