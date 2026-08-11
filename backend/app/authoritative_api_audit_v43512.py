from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib,json
from typing import Any
from .version import APP_VERSION
from . import authoritative_api_audit_v43511 as prior

VERSION=APP_VERSION; CONTRACT=prior.CONTRACT; AUDIT_DATE='2026-08-11'; ACCESS_CLASSES=prior.ACCESS_CLASSES
COMPLETED_CONNECTOR_TARGETS=tuple(prior.COMPLETED_CONNECTOR_TARGETS)+(
 {'id':'airnow','workspace':'Atmosphere, Air Quality & Aerosols','state':'AUTH_REQUIRED','completed_in':'4.35.12'},
 {'id':'copernicus-era5','workspace':'Climate Baselines, Anomalies & Extremes','state':'DISCOVERY','completed_in':'4.35.12'},
 {'id':'cams-global','workspace':'Atmosphere, Air Quality & Aerosols','state':'DISCOVERY','completed_in':'4.35.12'},
)
PRIORITY_CONNECTOR_TARGETS=tuple(x for x in prior.PRIORITY_CONNECTOR_TARGETS if x.get('id') not in {'airnow','copernicus-era5','cams-global'})
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def _configured(settings,name): return bool(str(getattr(settings,name,'') or '').strip()) if settings is not None else False

def source_inventory(settings:Any=None):
    rows=[dict(x) for x in prior.source_inventory(settings)]
    for r in rows:
        sid=r.get('source_id'); ws=r.get('workspace')
        if ws=='Atmosphere, Air Quality & Aerosols' and sid=='airnow':
            r.update(access_class='AUTH_REQUIRED',implementation_evidence='authoritative_connectors_v43512 bounded AirNow current-observation retrieval',configuration_key='SC_SI_AIRNOW_API_KEY',configuration_state='configured' if _configured(settings,'airnow_api_key') else 'configuration-required',authentication='free AirNow account API key')
        elif ws=='Climate Baselines, Anomalies & Extremes' and sid=='copernicus-era5':
            r.update(access_class='DISCOVERY',implementation_evidence='authoritative_connectors_v43512 public ECMWF CDS STAC collection discovery; authenticated CDS retrieval remains separate',configuration_state='configured',authentication='public catalogue; PAT required for data retrieval')
        elif ws=='Atmosphere, Air Quality & Aerosols' and sid=='cams-global':
            r.update(machine_readable=True,protocol='STAC / JSON',api_url='https://ads.atmosphere.copernicus.eu/api/catalogue/v1/collections/cams-global-atmospheric-composition-forecasts',access_class='DISCOVERY',implementation_evidence='authoritative_connectors_v43512 public ECMWF ADS STAC collection discovery; authenticated ADS retrieval remains separate',configuration_state='configured',authentication='public catalogue; account/PAT required for data retrieval')
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
    rows={r['workspace']:r for r in workspace_matrix(settings)['workspaces']}; climate=rows['Climate Baselines, Anomalies & Extremes']; atmosphere=rows['Atmosphere, Air Quality & Aerosols']
    return {'ok':climate['registered_backlog']==0 and atmosphere['registered_backlog']==0,'version':VERSION,'contract':'workspace-connector-closure-ii','network_calls_performed':False,'workspaces':{'climate':climate,'atmosphere':atmosphere},'climate_operational_without_credentials':climate['counts']['LIVE']>0,'atmosphere_discovery_without_credentials':atmosphere['counts']['DISCOVERY']>0,'atmosphere_current_observation_credentials_remaining':sum(1 for _ in range(atmosphere['counts']['AUTH_REQUIRED'])),'generated_at':_now()}
def audit_overview(settings=None):
    rows=source_inventory(settings); c=_counts(rows); machine=[r for r in rows if r.get('machine_readable')]; base=prior.audit_overview(settings)
    payload={'ok':True,'version':VERSION,'contract':CONTRACT,'audit_date':AUDIT_DATE,'classification':base['classification'],'summary':{'source_registrations':len(rows),'unique_source_endpoints_or_records':len({_unique(r) for r in rows}),'workspaces_with_source_registries':len({r['workspace'] for r in rows}),'machine_readable_registrations':len(machine),'implemented_or_configuration_gated_registrations':c['LIVE']+c['DISCOVERY']+c['AUTH_REQUIRED'],'counts':c,'registered_but_not_retrieved':c['REGISTERED'],'stale_implemented_connectors':c['STALE']},'principles':list(base.get('principles') or [])+['Climate and Atmosphere now have zero REGISTERED machine-interface backlog.','AirNow is preliminary current AQI evidence and remains distinct from regulatory AQS.','ERA5 and CAMS public catalogue interfaces are DISCOVERY; authenticated data retrieval remains a separate operation.'],'verified_machine_interfaces':list(base.get('verified_machine_interfaces') or []),'completed_connector_targets':list(COMPLETED_CONNECTOR_TARGETS),'priority_connector_targets':list(PRIORITY_CONNECTOR_TARGETS),'closure_ii':closure_status(settings),'generated_at':_now()}
    payload['audit_sha256']=_digest({'summary':payload['summary'],'closure_ii':payload['closure_ii']}); return payload
def audit_catalog(settings=None,workspace='',access_class='',query=''):
    rows=source_inventory(settings); w=(workspace or '').lower(); a=(access_class or '').upper(); q=(query or '').lower()
    if a and a not in ACCESS_CLASSES: raise ValueError('invalid access_class')
    if w: rows=[r for r in rows if w in r['workspace'].lower() or w==r['module'].lower()]
    if a: rows=[r for r in rows if r['access_class']==a]
    if q: rows=[r for r in rows if q in ' '.join(str(r.get(k) or '') for k in ('title','organization','host','source_id','protocol','workspace')).lower()]
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'count':len(rows),'counts':_counts(rows),'access_classes':list(ACCESS_CLASSES),'sources':rows,'generated_at':_now()}
def audit_readiness(settings=None):
    o=audit_overview(settings); cl=closure_status(settings)
    checks={'inventory_present':o['summary']['source_registrations']>=188,'zero_stale':o['summary']['counts']['STALE']==0,'climate_registered_backlog_zero':cl['workspaces']['climate']['registered_backlog']==0,'atmosphere_registered_backlog_zero':cl['workspaces']['atmosphere']['registered_backlog']==0,'network_free':True}
    return {'ok':all(checks.values()),'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'checks':checks,'closure_ii':cl,'generated_at':_now()}
