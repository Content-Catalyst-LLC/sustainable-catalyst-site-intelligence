from __future__ import annotations
"""v4.35.23 — High-Priority Workspace Connector Closure IV: Agriculture, Food Security & Humanitarian Conditions."""
from datetime import datetime, timezone
import re
from typing import Any
from urllib.parse import urlencode, quote

from .version import APP_VERSION
from . import authoritative_connectors_v43513 as prior
from .authoritative_connectors_v4355 import _request_json

VERSION=APP_VERSION
CONTRACT='high-priority-workspace-connector-closure-iv'

def _now(): return datetime.now(timezone.utc).isoformat()
def _timeout(settings): return int(getattr(settings,'external_request_timeout_seconds',8)) if settings is not None else 8
def _setting(settings,name,default=''):
    v=str(getattr(settings,name,'') or '').strip() if settings is not None else ''
    return v or default

def _clean(value,name,maxlen=80,pattern=r'[A-Za-z0-9_.+@:/ -]+'):
    v=(value or '').strip()
    if not v or len(v)>maxlen or not re.fullmatch(pattern,v): raise ValueError(f'{name} is invalid')
    return v

NEW_CONNECTORS=(
 {'id':'gdacs-events-v1','title':'GDACS Events API','organization':'Global Disaster Alert and Coordination System (United Nations / European Commission)','workspace':'Humanitarian Intelligence','mode':'LIVE','authentication':'public','boundary':'GDACS alerts and impact estimates are preliminary coordination evidence. Site Intelligence does not replace national warning authorities, issue evacuation instructions, or convert GDACS severity into an independent emergency declaration.'},
 {'id':'hdx-ckan-discovery','title':'Humanitarian Data Exchange CKAN API','organization':'OCHA Centre for Humanitarian Data','workspace':'Humanitarian / Conflict & Human Security','mode':'DISCOVERY','authentication':'public metadata discovery; some tabular resources require an HDX token','boundary':'HDX dataset/resource metadata is discovery evidence. Dataset presence is not a verified current humanitarian condition, and resource-level access/licensing/quality constraints remain attached.'},
 {'id':'hdx-hapi-food-security','title':'HDX HAPI Food Security','organization':'OCHA Centre for Humanitarian Data','workspace':'Humanitarian Intelligence / Food Security','mode':'AUTH_REQUIRED','authentication':'SC_SI_HDX_HAPI_APP_IDENTIFIER','boundary':'HDX HAPI standardizes source data and may apply p-code/name transformations. IPC phase, provider geography, reference period, warnings and source-resource identifiers remain visible; HAPI records are not a new Site Intelligence classification.'},
 {'id':'ipc-food-security-api','title':'IPC-CH Public API','organization':'Integrated Food Security Phase Classification','workspace':'Agriculture, Crops & Food Systems / Food Security','mode':'AUTH_REQUIRED','authentication':'SC_SI_IPC_API_KEY','boundary':'IPC/CH classifications are source-governed analytical classifications for defined areas and periods. Site Intelligence does not create, upgrade, downgrade, interpolate or extend IPC phases beyond the published analysis.'},
 {'id':'fews-net-data-platform','title':'FEWS NET Data Warehouse REST API','organization':'Famine Early Warning Systems Network','workspace':'Agriculture, Crops & Food Systems / Food Security','mode':'LIVE','authentication':'public data works without authentication; optional FEWS NET account expands permissioned coverage','boundary':'FEWS NET current and projected food-security classifications, population estimates and market-price records retain scenario, collection date, geography, units and source metadata. Projections are not observations and FEWS NET analyses are not silently relabeled as IPC-issued classifications.'},
)
CONNECTORS=tuple(prior.CONNECTORS)+NEW_CONNECTORS
for _name in [n for n in dir(prior) if not n.startswith('_') and callable(getattr(prior,n)) and n not in {'connector_catalog','connector_readiness'}]:
    if _name not in globals(): globals()[_name]=getattr(prior,_name)

def connector_catalog(settings=None):
    rows=[dict(x) for x in prior.connector_catalog(settings)['connectors']]
    for c in NEW_CONNECTORS:
        r=dict(c); r['network_check_performed']=False; r['configuration_key']=None; r['credential_configured']=True
        if c['id']=='hdx-hapi-food-security':
            r['configuration_key']='SC_SI_HDX_HAPI_APP_IDENTIFIER'; r['credential_configured']=bool(_setting(settings,'hdx_hapi_app_identifier'))
        elif c['id']=='ipc-food-security-api':
            r['configuration_key']='SC_SI_IPC_API_KEY'; r['credential_configured']=bool(_setting(settings,'ipc_api_key'))
        rows.append(r)
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'connector_count':len(rows),'live_connector_count':sum(x['mode']=='LIVE' for x in rows),'discovery_connector_count':sum(x['mode']=='DISCOVERY' for x in rows),'auth_required_connector_count':sum(x['mode']=='AUTH_REQUIRED' for x in rows),'configured_auth_required_connector_count':sum(x['mode']=='AUTH_REQUIRED' and x.get('credential_configured') for x in rows),'closure_iv_connector_count':5,'connectors':rows,'principles':['Agriculture/Food Security and Humanitarian Intelligence have zero ambiguous REGISTERED machine-interface backlog after closure IV.','Operational humanitarian evidence remains semantically distinct from long-run agriculture statistics and modeled/projected food-security conditions.','Discovery metadata is never promoted to an observation.','Upstream availability remains non-blocking for deployment.'],'generated_at':_now()}

def connector_readiness(settings=None):
    c=connector_catalog(settings); ids={x['id'] for x in c['connectors']}; expected={x['id'] for x in NEW_CONNECTORS}
    checks={'forty_five_interfaces_registered':c['connector_count']==45,'twenty_eight_live':c['live_connector_count']==28,'nine_discovery':c['discovery_connector_count']==9,'eight_auth_required':c['auth_required_connector_count']==8,'closure_iv_ids_present':expected.issubset(ids),'network_free':True,'upstream_health_non_blocking':True}
    return {'ok':all(checks.values()),'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'checks':checks,'generated_at':_now()}

def gdacs_events(settings, *, event_type:str='', alert_level:str='', limit:int=50):
    limit=int(limit)
    if not 1<=limit<=100: raise ValueError('limit must be between 1 and 100')
    params={'pagesize':limit,'pagenumber':1}
    if event_type:
        ev=_clean(event_type,'event_type',8,r'[A-Za-z]+').upper()
        if ev not in {'EQ','TC','FL','VO','WF','DR'}: raise ValueError('unsupported GDACS event_type')
        params['eventtype']=ev
    if alert_level:
        al=_clean(alert_level,'alert_level',8,r'[A-Za-z]+').lower()
        if al not in {'green','orange','red'}: raise ValueError('unsupported GDACS alert_level')
        params['alertlevel']=al
    base=_setting(settings,'gdacs_api_base_url','https://www.gdacs.org/gdacsapi/api').rstrip('/')
    endpoint=f"{base}/Events/geteventlist/latest?{urlencode(params)}"
    payload=_request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'gdacs-events-v1','mode':'LIVE','query':{'event_type':event_type or None,'alert_level':alert_level or None,'limit':limit},'data':payload,'provenance':{'organization':'Global Disaster Alert and Coordination System','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[0]['boundary']}

def hdx_dataset_search(settings, *, query:str, rows:int=20):
    q=_clean(query,'query',120,r"[A-Za-z0-9_.+@:/,'() -]+")
    rows=int(rows)
    if not 1<=rows<=50: raise ValueError('rows must be between 1 and 50')
    base=_setting(settings,'hdx_ckan_base_url','https://data.humdata.org/api/action').rstrip('/')
    endpoint=f"{base}/package_search?{urlencode({'q':q,'rows':rows})}"
    payload=_request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'hdx-ckan-discovery','mode':'DISCOVERY','query':{'q':q,'rows':rows},'data':payload,'provenance':{'organization':'OCHA Centre for Humanitarian Data','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[1]['boundary']}

_HAPI_ENDPOINTS={
 'food-security':'food-security-nutrition-poverty/food-security',
 'food-prices':'food-security-nutrition-poverty/food-prices-market-monitor',
}
def hdx_hapi(settings, *, dataset:str='food-security', location_code:str='', limit:int=100, offset:int=0):
    app_id=_setting(settings,'hdx_hapi_app_identifier')
    if not app_id:
        return {'ok':False,'version':VERSION,'connector_id':'hdx-hapi-food-security','mode':'AUTH_REQUIRED','configuration_required':True,'configuration_key':'SC_SI_HDX_HAPI_APP_IDENTIFIER','network_calls_performed':False,'boundary':NEW_CONNECTORS[2]['boundary']}
    if dataset not in _HAPI_ENDPOINTS: raise ValueError('unsupported HDX HAPI dataset')
    limit=int(limit); offset=int(offset)
    if not 1<=limit<=500 or not 0<=offset<=100000: raise ValueError('invalid HDX HAPI pagination')
    params={'app_identifier':app_id,'output_format':'json','limit':limit,'offset':offset}
    if location_code:
        loc=_clean(location_code,'location_code',3,r'[A-Za-z]{3}').upper(); params['location_code']=loc
    base=_setting(settings,'hdx_hapi_base_url','https://hapi.humdata.org/api/v2').rstrip('/')
    endpoint=f"{base}/{_HAPI_ENDPOINTS[dataset]}?{urlencode(params)}"
    payload=_request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'hdx-hapi-food-security','mode':'AUTH_REQUIRED','dataset':dataset,'data':payload,'provenance':{'organization':'OCHA Centre for Humanitarian Data','endpoint':endpoint.replace(app_id,'REDACTED'),'retrieved_at':_now()},'boundary':NEW_CONNECTORS[2]['boundary']}

_IPC_RESOURCES={'analyses','country','population','areas','points'}
def ipc_food_security(settings, *, resource:str='country', country:str='', year:int|None=None, analysis_type:str='', limit:int=250):
    key=_setting(settings,'ipc_api_key')
    if not key:
        return {'ok':False,'version':VERSION,'connector_id':'ipc-food-security-api','mode':'AUTH_REQUIRED','configuration_required':True,'configuration_key':'SC_SI_IPC_API_KEY','network_calls_performed':False,'boundary':NEW_CONNECTORS[3]['boundary']}
    resource=(resource or '').strip().lower()
    if resource not in _IPC_RESOURCES: raise ValueError('unsupported IPC resource')
    limit=int(limit)
    if not 1<=limit<=1000: raise ValueError('limit must be between 1 and 1000')
    params={'key':key,'format':'json'}
    if country: params['country']=_clean(country,'country',2,r'[A-Za-z]{2}').upper()
    if year is not None:
        y=int(year)
        if y<2000 or y>2100: raise ValueError('year is out of bounds')
        params['year']=y
    if analysis_type:
        t=_clean(analysis_type,'analysis_type',1,r'[ACac]').upper(); params['type']=t
    base=_setting(settings,'ipc_api_base_url','https://api.ipcinfo.org').rstrip('/')
    endpoint=f"{base}/{quote(resource)}?{urlencode(params)}"
    payload=_request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'ipc-food-security-api','mode':'AUTH_REQUIRED','resource':resource,'data':payload,'provenance':{'organization':'Integrated Food Security Phase Classification','endpoint':endpoint.replace(key,'REDACTED'),'retrieved_at':_now()},'boundary':NEW_CONNECTORS[3]['boundary']}

_FEWS_ENDPOINTS={'market-prices':'marketpricefacts','food-security-phase':'ipcphase','food-insecure-population':'ipcpopulationsize','cross-border-trade':'tradeflowquantityvalue'}
def fews_net_data(settings, *, dataset:str='food-security-phase', country_code:str='', start_date:str='', end_date:str='', scenario:str='', page_size:int=100, offset:int=0):
    if dataset not in _FEWS_ENDPOINTS: raise ValueError('unsupported FEWS NET dataset')
    page_size=int(page_size); offset=int(offset)
    if not 1<=page_size<=500 or not 0<=offset<=100000: raise ValueError('invalid FEWS NET pagination')
    if not any((country_code,start_date,end_date,scenario)):
        raise ValueError('FEWS NET retrieval requires at least one bounded geography/date/scenario filter')
    params={'format':'json','fields':'simple','page_size':page_size,'offset':offset}
    if country_code: params['country_code']=_clean(country_code,'country_code',2,r'[A-Za-z]{2}').upper()
    for name,val in [('start_date',start_date),('end_date',end_date)]:
        if val:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',val): raise ValueError(f'{name} must be YYYY-MM-DD')
            params[name]=val
    if scenario:
        sc=_clean(scenario,'scenario',8,r'[A-Za-z0-9]+').upper()
        if dataset in {'food-security-phase','food-insecure-population'} and sc not in {'CS','ML1','ML2','FIPE6'}: raise ValueError('unsupported FEWS NET scenario')
        params['scenario']=sc
    base=_setting(settings,'fews_net_api_base_url','https://fdw.fews.net/api').rstrip('/')
    endpoint=f"{base}/{_FEWS_ENDPOINTS[dataset]}/?{urlencode(params)}"
    payload=_request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'fews-net-data-platform','mode':'LIVE','dataset':dataset,'query':{k:v for k,v in params.items() if k not in {'format','fields'}},'data':payload,'provenance':{'organization':'Famine Early Warning Systems Network','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[4]['boundary']}
