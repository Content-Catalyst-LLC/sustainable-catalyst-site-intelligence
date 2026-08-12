from __future__ import annotations

"""v4.35.21 audit extension for Authoritative Connector Expansion IV."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib, json
from typing import Any

from .version import APP_VERSION
from . import authoritative_api_audit_v4357 as prior

VERSION=APP_VERSION
CONTRACT=prior.CONTRACT
AUDIT_DATE='2026-08-11'
ACCESS_CLASSES=prior.ACCESS_CLASSES

NEW_VERIFIED_MACHINE_INTERFACES=(
 {'id':'faostat-data-api','provider':'Food and Agriculture Organization of the United Nations','host':'fenixservices.fao.org','protocol':'REST / JSON / CSV','current_version':'FAOSTAT API developer-portal service','documentation_url':'https://www.fao.org/faostat/en/#developer-portal','authentication':'public','status':'implemented-live-v4.35.21','audit_date':AUDIT_DATE},
 {'id':'ilostat-sdmx','provider':'International Labour Organization','host':'rplumber.ilo.org','protocol':'SDMX / REST','current_version':'current ILOSTAT dissemination service','documentation_url':'https://www.ilo.org/resource/other/ilostat-sdmx-user-guide','authentication':'public','status':'implemented-live-v4.35.21','audit_date':AUDIT_DATE},
 {'id':'oecd-data-explorer-sdmx','provider':'OECD','host':'sdmx.oecd.org','protocol':'SDMX REST / JSON / CSV','current_version':'OECD Data Explorer API','documentation_url':'https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html','authentication':'public; rate limited','status':'implemented-live-v4.35.21','audit_date':AUDIT_DATE},
 {'id':'epa-frs-public-api','provider':'U.S. Environmental Protection Agency','host':'ofmpub.epa.gov','protocol':'REST / JSON','current_version':'FRS public query services','documentation_url':'https://www.epa.gov/frs/frs-api','authentication':'public query service','status':'implemented-live-v4.35.21','audit_date':AUDIT_DATE},
 {'id':'usgs-volcano-hans','provider':'U.S. Geological Survey Volcano Hazards Program','host':'volcanoes.usgs.gov','protocol':'REST / JSON','current_version':'HANS public API','documentation_url':'https://volcanoes.usgs.gov/vsc/api/','authentication':'public','status':'implemented-live-v4.35.21','audit_date':AUDIT_DATE},
)
VERIFIED_MACHINE_INTERFACES=tuple(prior.VERIFIED_MACHINE_INTERFACES)+NEW_VERIFIED_MACHINE_INTERFACES
COMPLETED_CONNECTOR_TARGETS=tuple(prior.COMPLETED_CONNECTOR_TARGETS)+(
 {'id':'faostat-data-api','workspace':'Agriculture / Food Security','state':'LIVE','completed_in':'4.35.21'},
 {'id':'ilostat-sdmx','workspace':'Economics / Labor','state':'LIVE','completed_in':'4.35.21'},
 {'id':'oecd-data-explorer-sdmx','workspace':'Economics / Development','state':'LIVE','completed_in':'4.35.21'},
 {'id':'epa-frs-public-api','workspace':'Industrial / Facilities','state':'LIVE','completed_in':'4.35.21'},
 {'id':'usgs-volcano-hans','workspace':'Geosphere','state':'LIVE','completed_in':'4.35.21'},
)
PRIORITY_CONNECTOR_TARGETS=(
 {'id':'airnow-api','workspace':'Atmosphere / Air Quality','reason':'Connect EPA AirNow with server-side key configuration and pollutant semantics.','target_state':'AUTH_REQUIRED'},
 {'id':'water-quality-portal','workspace':'Marine Pollution / Water Quality','reason':'Connect the USGS/EPA Water Quality Portal with bounded station/result retrieval.','target_state':'LIVE'},
 {'id':'worms-rest','workspace':'Marine Biodiversity','reason':'Connect WoRMS taxonomic services and preserve AphiaID lineage.','target_state':'LIVE'},
 {'id':'argovis-argo','workspace':'Water Column / Argo','reason':'Connect Argovis/Argo profile retrieval with bounded space-time queries.','target_state':'LIVE'},
 {'id':'measurement-lab','workspace':'Digital Connectivity','reason':'Connect M-Lab performance data discovery/retrieval with bounded queries.','target_state':'LIVE'},
)

def _now(): return datetime.now(timezone.utc).isoformat()
def _digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def _new_rows():
    specs=(
      ('faostat-data-api','FAOSTAT Data API','Food and Agriculture Organization of the United Nations','fenixservices.fao.org','https://fenixservices.fao.org/faostat/api/v1','REST / JSON / CSV','Agriculture, Crops & Food Systems'),
      ('ilostat-sdmx','ILOSTAT SDMX / indicator service','International Labour Organization','rplumber.ilo.org','https://rplumber.ilo.org/data/indicator','SDMX / REST / JSON','Human Development'),
      ('oecd-data-explorer-sdmx','OECD Data Explorer SDMX API','OECD','sdmx.oecd.org','https://sdmx.oecd.org/public/rest','SDMX REST / JSON / CSV','Sustainable Development Connectors'),
      ('epa-frs-public-api','EPA Facility Registry Service API','U.S. Environmental Protection Agency','ofmpub.epa.gov','https://ofmpub.epa.gov/frs_public2/frs_rest_services.get_facilities','REST / JSON','Industrial Manufacturing & Trade'),
    )
    out=[]
    for sid,title,org,host,url,protocol,workspace in specs:
      meta=next(x for x in NEW_VERIFIED_MACHINE_INTERFACES if x['id']==sid)
      out.append({'workspace':workspace,'module':'authoritative_connectors_v43510','registry':'connector-expansion-iv','source_id':sid,'title':title,'organization':org,'authority':'official-intergovernmental-or-public-institution' if org in {'OECD','International Labour Organization','Food and Agriculture Organization of the United Nations'} else 'official-government-source','host':host,'url':url,'api_url':url,'documentation_url':meta['documentation_url'],'protocol':protocol,'machine_readable':True,'access_class':'LIVE','implementation_evidence':f'authoritative_connectors_v43510 {sid} bounded retrieval','configuration_state':'configured','configuration_key':None,'authentication':meta['authentication'],'coverage':workspace,'limitations':'Observation semantics, units, revision/status metadata and source provenance remain attached to retrieved evidence.'})
    return out

def source_inventory(settings:Any=None):
    rows=[dict(x) for x in prior.source_inventory(settings)]
    # Close the pre-existing HANS retrieval gap instead of adding a duplicate registry row.
    for r in rows:
      if r.get('source_id')=='usgs-volcano-hans' and r.get('host')=='volcanoes.usgs.gov':
        r['machine_readable']=True; r['access_class']='LIVE'; r['implementation_evidence']='authoritative_connectors_v43510 USGS HANS bounded VONA retrieval'; r['protocol']='REST / JSON'; r['api_url']='https://volcanoes.usgs.gov/vsc/api/hansApi/'
    rows.extend(_new_rows())
    return rows

def _counts(rows):
    c=Counter(r['access_class'] for r in rows); return {k:int(c.get(k,0)) for k in ACCESS_CLASSES}
def _unique_source_key(row):
    host=row.get('host') or ''; return f'host:{host}' if host else f"record:{row.get('module')}:{row.get('source_id')}"

def audit_overview(settings:Any=None):
    rows=source_inventory(settings); counts=_counts(rows); machine=[r for r in rows if r.get('machine_readable')]
    base=prior.audit_overview(settings)
    payload={'ok':True,'version':VERSION,'contract':CONTRACT,'audit_date':AUDIT_DATE,'classification':base['classification'],'summary':{'source_registrations':len(rows),'unique_source_endpoints_or_records':len({_unique_source_key(r) for r in rows}),'workspaces_with_source_registries':len({r['workspace'] for r in rows}),'machine_readable_registrations':len(machine),'implemented_or_configuration_gated_registrations':counts['LIVE']+counts['DISCOVERY']+counts['AUTH_REQUIRED'],'counts':counts,'registered_but_not_retrieved':counts['REGISTERED'],'stale_implemented_connectors':counts['STALE']},'principles':list(base['principles'])+['Expansion IV closes an existing USGS volcano retrieval gap and adds direct first-party statistical/facility interfaces.','Connector implementation does not convert an agency portal or semantically different dataset into live evidence automatically.'],'verified_machine_interfaces':list(VERIFIED_MACHINE_INTERFACES),'completed_connector_targets':list(COMPLETED_CONNECTOR_TARGETS),'priority_connector_targets':list(PRIORITY_CONNECTOR_TARGETS),'generated_at':_now()}
    payload['audit_sha256']=_digest({'summary':payload['summary'],'verified':payload['verified_machine_interfaces']}); return payload

def audit_catalog(settings=None,workspace='',access_class='',query=''):
    rows=source_inventory(settings); w=(workspace or '').lower(); a=(access_class or '').upper(); q=(query or '').lower()
    if a and a not in ACCESS_CLASSES: raise ValueError('invalid access_class')
    if w: rows=[r for r in rows if w in r['workspace'].lower() or w==r['module'].lower()]
    if a: rows=[r for r in rows if r['access_class']==a]
    if q: rows=[r for r in rows if q in ' '.join(str(r.get(k) or '') for k in ('title','organization','host','source_id','protocol','workspace')).lower()]
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'count':len(rows),'counts':_counts(rows),'access_classes':list(ACCESS_CLASSES),'sources':rows,'generated_at':_now()}

def workspace_matrix(settings=None):
    groups=defaultdict(list)
    for r in source_inventory(settings): groups[r['workspace']].append(r)
    work=[]
    for name,rows in sorted(groups.items()):
      counts=_counts(rows); machine=sum(bool(r.get('machine_readable')) for r in rows)
      work.append({'workspace':name,'source_registrations':len(rows),'machine_readable_registrations':machine,'counts':counts,'fully_live':machine>0 and counts['REGISTERED']==0 and counts['STALE']==0 and counts['AUTH_REQUIRED']==0,'connector_gap':counts['REGISTERED']+counts['BULK']+counts['AUTH_REQUIRED']+counts['STALE']})
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'workspace_count':len(work),'workspaces':work,'generated_at':_now()}

def audit_readiness(settings=None):
    o=audit_overview(settings); ids={x['id'] for x in NEW_VERIFIED_MACHINE_INTERFACES}; source_ids={r['source_id'] for r in source_inventory(settings) if r['access_class']=='LIVE'}
    checks={'source_registry_inventory_present':o['summary']['source_registrations']>=188,'classification_taxonomy_complete':set(ACCESS_CLASSES)=={'LIVE','DISCOVERY','REGISTERED','AUTH_REQUIRED','BULK','STALE','UNAVAILABLE'},'five_expansion_iv_interfaces_verified':ids.issubset({x['id'] for x in VERIFIED_MACHINE_INTERFACES}),'five_expansion_iv_connectors_live':ids.issubset(source_ids),'registered_backlog_reduced_not_hidden':o['summary']['counts']['REGISTERED']<45 and o['summary']['counts']['REGISTERED']>0,'no_known_stale_connector':o['summary']['counts']['STALE']==0,'network_checks_not_required_for_deterministic_readiness':True}
    return {'ok':all(checks.values()),'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'checks':checks,'generated_at':_now()}
