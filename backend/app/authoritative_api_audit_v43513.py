from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib,json
from typing import Any
from .version import APP_VERSION
from . import authoritative_api_audit_v43512 as prior

VERSION=APP_VERSION; CONTRACT=prior.CONTRACT; AUDIT_DATE='2026-08-11'; ACCESS_CLASSES=prior.ACCESS_CLASSES
COMPLETED_CONNECTOR_TARGETS=tuple(prior.COMPLETED_CONNECTOR_TARGETS)+(
 {'id':'osm-water-infrastructure','workspace':'Water, Wastewater & Sanitation','state':'LIVE','completed_in':'4.35.21'},
 {'id':'epa-sdwis-drinking-water','workspace':'Water, Wastewater & Sanitation','state':'LIVE','completed_in':'4.35.21'},
 {'id':'drought-gov','workspace':'Hydrology, Rivers, Flood & Drought','state':'LIVE','completed_in':'4.35.21'},
 {'id':'nasa-gpm-imerg','workspace':'Hydrology, Rivers, Flood & Drought','state':'DISCOVERY','completed_in':'4.35.21'},
 {'id':'copernicus-glofas','workspace':'Hydrology, Rivers, Flood & Drought','state':'DISCOVERY','completed_in':'4.35.21'},
)
PRIORITY_CONNECTOR_TARGETS=tuple(x for x in prior.PRIORITY_CONNECTOR_TARGETS if x.get('id') not in {'osm-water-infrastructure','epa-sdwis-drinking-water','drought-gov','nasa-gpm-imerg','copernicus-glofas'})
def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def source_inventory(settings:Any=None):
    rows=[dict(x) for x in prior.source_inventory(settings)]
    for r in rows:
        sid=r.get('source_id'); ws=r.get('workspace')
        if ws=='Water, Wastewater & Sanitation' and sid=='openstreetmap-water-infrastructure':
            r.update(access_class='LIVE',implementation_evidence='authoritative_connectors_v43513 bounded OSM/Overpass water-infrastructure retrieval',configuration_state='configured',authentication='public')
        elif ws=='Water, Wastewater & Sanitation' and sid=='epa-sdwis-drinking-water':
            r.update(access_class='LIVE',protocol='REST / JSON',api_url='https://data.epa.gov/efservice/',implementation_evidence='authoritative_connectors_v43513 bounded EPA SDWIS/Envirofacts retrieval',configuration_state='configured',authentication='public')
        elif ws=='Hydrology, Rivers, Flood & Drought' and sid=='drought-gov':
            r.update(access_class='LIVE',protocol='JSON / GeoJSON / TopoJSON',api_url='https://storage.googleapis.com/noaa-nidis-drought-gov-data/current-conditions/json/v1/',implementation_evidence='authoritative_connectors_v43513 bounded public Drought.gov/NIDIS object retrieval',configuration_state='configured',authentication='public')
        elif ws=='Hydrology, Rivers, Flood & Drought' and sid=='nasa-gpm-imerg':
            r.update(machine_readable=True,protocol='CMR / JSON',api_url='https://cmr.earthdata.nasa.gov/search/collections.json',access_class='DISCOVERY',implementation_evidence='authoritative_connectors_v43513 NASA EOSDIS CMR discovery constrained to GPM IMERG',configuration_state='configured',authentication='public discovery; Earthdata login may be required for scientific file retrieval')
        elif ws=='Hydrology, Rivers, Flood & Drought' and sid=='copernicus-glofas':
            r.update(machine_readable=True,protocol='REST / JSON',api_url='https://european-flood.emergency.copernicus.eu/api/fms/download/glofas/',access_class='DISCOVERY',implementation_evidence='authoritative_connectors_v43513 public GloFAS product-layer discovery; EWDS retrieval remains separate',configuration_state='configured',authentication='public layer discovery; EWDS/API credentials may be required for data retrieval')
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
    rows={r['workspace']:r for r in workspace_matrix(settings)['workspaces']}; hydrology=rows['Hydrology, Rivers, Flood & Drought']; water=rows['Water, Wastewater & Sanitation']
    return {'ok':hydrology['registered_backlog']==0 and water['registered_backlog']==0,'version':VERSION,'contract':'workspace-connector-closure-iii','network_calls_performed':False,'workspaces':{'hydrology':hydrology,'water_sanitation':water},'hydrology_live_without_credentials':hydrology['counts']['LIVE']>0,'water_sanitation_live_without_credentials':water['counts']['LIVE']>0,'generated_at':_now()}
def audit_overview(settings=None):
    rows=source_inventory(settings); c=_counts(rows); machine=[r for r in rows if r.get('machine_readable')]; base=prior.audit_overview(settings)
    payload={'ok':True,'version':VERSION,'contract':CONTRACT,'audit_date':AUDIT_DATE,'classification':base['classification'],'summary':{'source_registrations':len(rows),'unique_source_endpoints_or_records':len({_unique(r) for r in rows}),'workspaces_with_source_registries':len({r['workspace'] for r in rows}),'machine_readable_registrations':len(machine),'implemented_or_configuration_gated_registrations':c['LIVE']+c['DISCOVERY']+c['AUTH_REQUIRED'],'counts':c,'registered_but_not_retrieved':c['REGISTERED'],'stale_implemented_connectors':c['STALE']},'principles':list(base.get('principles') or [])+['Hydrology and Water/Wastewater/Sanitation now have zero REGISTERED machine-interface backlog.','SDWIS records remain distinct from real-time tap-water safety and household service.','GPM CMR and GloFAS public-layer interfaces are DISCOVERY; metadata/layer presence is never promoted to an observation or warning.'],'verified_machine_interfaces':list(base.get('verified_machine_interfaces') or []),'completed_connector_targets':list(COMPLETED_CONNECTOR_TARGETS),'priority_connector_targets':list(PRIORITY_CONNECTOR_TARGETS),'closure_iii':closure_status(settings),'generated_at':_now()}
    payload['audit_sha256']=_digest({'summary':payload['summary'],'closure_iii':payload['closure_iii']}); return payload
def audit_catalog(settings=None,workspace='',access_class='',query=''):
    rows=source_inventory(settings); w=(workspace or '').lower(); a=(access_class or '').upper(); q=(query or '').lower()
    if a and a not in ACCESS_CLASSES: raise ValueError('invalid access_class')
    if w: rows=[r for r in rows if w in r['workspace'].lower() or w==r['module'].lower()]
    if a: rows=[r for r in rows if r['access_class']==a]
    if q: rows=[r for r in rows if q in ' '.join(str(r.get(k) or '') for k in ('title','organization','host','source_id','protocol','workspace')).lower()]
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'count':len(rows),'counts':_counts(rows),'access_classes':list(ACCESS_CLASSES),'sources':rows,'generated_at':_now()}
def audit_readiness(settings=None):
    o=audit_overview(settings); cl=closure_status(settings)
    checks={'inventory_present':o['summary']['source_registrations']>=188,'zero_stale':o['summary']['counts']['STALE']==0,'hydrology_registered_backlog_zero':cl['workspaces']['hydrology']['registered_backlog']==0,'water_sanitation_registered_backlog_zero':cl['workspaces']['water_sanitation']['registered_backlog']==0,'network_free':True}
    return {'ok':all(checks.values()),'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'checks':checks,'closure_iii':cl,'generated_at':_now()}
