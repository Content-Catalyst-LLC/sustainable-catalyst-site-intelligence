from __future__ import annotations
"""v4.35.20 — High-Priority Workspace Connector Closure I: Energy & Digital Infrastructure."""
from datetime import datetime, timezone
import re
from typing import Any
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .version import APP_VERSION
from .external_resilience_v43517 import request_text as resilient_request_text
from . import authoritative_connectors_v43510 as prior
from .authoritative_connectors_v4355 import _request_json, MAX_RESPONSE_BYTES

VERSION=APP_VERSION
CONTRACT='high-priority-workspace-connector-closure-i'

def _now(): return datetime.now(timezone.utc).isoformat()
def _timeout(settings): return int(getattr(settings,'external_request_timeout_seconds',8)) if settings is not None else 8
def _setting(settings,name,default=''):
    v=str(getattr(settings,name,'') or '').strip() if settings is not None else ''
    return v or default

def _request_text(url:str, *, timeout:int=8, max_bytes:int=MAX_RESPONSE_BYTES)->str:
    return resilient_request_text(url, headers={'Accept':'application/xml,text/xml,text/plain;q=0.8'}, timeout=timeout, max_bytes=max_bytes, cache=True, stale_if_error=False)

NEW_CONNECTORS=(
 {'id':'osm-power-overpass','title':'OpenStreetMap Power Infrastructure via Overpass','organization':'OpenStreetMap contributors / Overpass','workspace':'Energy Infrastructure & Power Systems','mode':'LIVE','authentication':'public','boundary':'Community-mapped infrastructure evidence is supplemental and does not establish ownership, energization, operating status, capacity, reliability, safety or legal access.'},
 {'id':'eia-electricity-v2','title':'U.S. EIA Open Data API v2','organization':'U.S. Energy Information Administration','workspace':'Energy Infrastructure & Power Systems','mode':'AUTH_REQUIRED','authentication':'SC_SI_EIA_API_KEY','boundary':'EIA observations and forecasts retain route, facets, period, units and revision context; forecast demand is not actual demand and reported capacity is not real-time available capacity.'},
 {'id':'ember-electricity-v1','title':'Ember Electricity Data API v1','organization':'Ember','workspace':'Energy Infrastructure & Power Systems','mode':'AUTH_REQUIRED','authentication':'SC_SI_EMBER_API_KEY','boundary':'Ember is a harmonized statistical source, not real-time grid telemetry; country/month values do not establish local service continuity or outage status.'},
 {'id':'entsoe-transparency-web-api','title':'ENTSO-E Transparency Platform Web API','organization':'ENTSO-E','workspace':'Energy Infrastructure & Power Systems','mode':'AUTH_REQUIRED','authentication':'SC_SI_ENTSOE_SECURITY_TOKEN','boundary':'ENTSO-E market/system publications preserve bidding-zone, process and document semantics; unavailability records are source publications, not Site Intelligence outage declarations.'},
 {'id':'osm-telecom-overpass','title':'OpenStreetMap Telecommunications Infrastructure via Overpass','organization':'OpenStreetMap contributors / Overpass','workspace':'Digital Connectivity','mode':'LIVE','authentication':'public','boundary':'Mapped telecom infrastructure is supplemental evidence and does not prove coverage, current operation, signal strength, service availability, ownership or legal access.'},
 {'id':'mlab-locate-v2','title':'Measurement Lab Locate API v2','organization':'Measurement Lab','workspace':'Digital Connectivity','mode':'DISCOVERY','authentication':'public','boundary':'Locate v2 discovers nearby measurement services; it is not historical performance evidence and does not establish universal local speed, outage status, provider compliance or service availability.'},
 {'id':'fcc-bdc-public-data','title':'FCC Broadband Data Collection Public Data API','organization':'U.S. Federal Communications Commission','workspace':'Digital Connectivity','mode':'DISCOVERY','authentication':'public','boundary':'FCC BDC availability is provider-reported availability/coverage evidence, not measured performance, adoption, affordability or guaranteed installability. Discovery endpoints identify official release vintages/download surfaces.'},
)
CONNECTORS=tuple(prior.CONNECTORS)+NEW_CONNECTORS
for _name in [n for n in dir(prior) if not n.startswith('_') and callable(getattr(prior,n)) and n not in {'connector_catalog','connector_readiness'}]:
    if _name not in globals(): globals()[_name]=getattr(prior,_name)

def connector_catalog(settings=None):
    rows=[dict(x) for x in prior.connector_catalog(settings)['connectors']]
    for c in NEW_CONNECTORS:
        r=dict(c); key=c['authentication'] if c['authentication'].startswith('SC_SI_') else None
        configured=True if not key else bool(_setting(settings,key.removeprefix('SC_SI_').lower()))
        r.update({'credential_configured':configured,'configuration_key':key,'network_check_performed':False})
        rows.append(r)
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'connector_count':len(rows),'live_connector_count':sum(x['mode']=='LIVE' for x in rows),'discovery_connector_count':sum(x['mode']=='DISCOVERY' for x in rows),'auth_required_connector_count':sum(x['mode']=='AUTH_REQUIRED' for x in rows),'configured_auth_required_connector_count':sum(x['mode']=='AUTH_REQUIRED' and x.get('credential_configured') for x in rows),'closure_i_connector_count':7,'connectors':rows,'principles':['Energy and Digital registered-backlog closure is distinct from credential completion.','Community-mapped OSM evidence remains supplemental; official statistical/operational sources retain precedence.','Discovery interfaces are never presented as observations.','Upstream availability remains non-blocking for deployment.'],'generated_at':_now()}

def connector_readiness(settings=None):
    c=connector_catalog(settings); ids={x['id'] for x in c['connectors']}; expected={x['id'] for x in NEW_CONNECTORS}
    checks={'thirty_two_interfaces_registered':c['connector_count']==32,'twenty_three_live':c['live_connector_count']==23,'four_discovery':c['discovery_connector_count']==4,'five_auth_required':c['auth_required_connector_count']==5,'closure_i_ids_present':expected.issubset(ids),'network_free':True,'upstream_health_non_blocking':True}
    return {'ok':all(checks.values()),'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'checks':checks,'generated_at':_now()}

def _point(lat,lon,radius_km):
    lat=float(lat); lon=float(lon); radius=float(radius_km)
    if not -90<=lat<=90 or not -180<=lon<=180 or not 0<radius<=50: raise ValueError('latitude/longitude/radius are out of bounds')
    return lat,lon,radius

def _overpass(settings,lat,lon,radius_km,selector,connector_id,boundary):
    lat,lon,radius=_point(lat,lon,radius_km); r=int(round(radius*1000))
    query=f'[out:json][timeout:20];(node(around:{r},{lat},{lon})[{selector}];way(around:{r},{lat},{lon})[{selector}];relation(around:{r},{lat},{lon})[{selector}];);out center tags qt 250;'
    base=_setting(settings,'overpass_api_base_url','https://overpass-api.de/api/interpreter')
    endpoint=f'{base}?{urlencode({"data":query})}'; data=_request_json(endpoint,timeout=_timeout(settings))
    elements=(data.get('elements') or []) if isinstance(data,dict) else []
    return {'ok':True,'version':VERSION,'connector_id':connector_id,'mode':'LIVE','query':{'latitude':lat,'longitude':lon,'radius_km':radius},'record_count':len(elements),'data':elements[:250],'provenance':{'organization':'OpenStreetMap contributors / Overpass','endpoint':endpoint,'retrieved_at':_now()},'boundary':boundary}

def osm_power(settings, *, latitude:float, longitude:float, radius_km:float=10): return _overpass(settings,latitude,longitude,radius_km,'power','osm-power-overpass',NEW_CONNECTORS[0]['boundary'])
def osm_telecom(settings, *, latitude:float, longitude:float, radius_km:float=10): return _overpass(settings,latitude,longitude,radius_km,'communication:mobile_phone','osm-telecom-overpass',NEW_CONNECTORS[4]['boundary'])

def eia_electricity(settings, *, route:str='electricity/rto/region-data', data_field:str='value', facet_name:str='', facet_value:str='', frequency:str='hourly', start:str='', end:str='', length:int=100):
    key=_setting(settings,'eia_api_key')
    if not key: return {'ok':False,'version':VERSION,'connector_id':'eia-electricity-v2','mode':'AUTH_REQUIRED','configuration_required':True,'configuration_key':'SC_SI_EIA_API_KEY','network_calls_performed':False}
    route=(route or '').strip().strip('/')
    if not route.startswith('electricity/') or not re.fullmatch(r'[A-Za-z0-9_./-]+',route): raise ValueError('EIA route must be a bounded electricity/* API v2 route')
    if not 1<=int(length)<=500: raise ValueError('length must be between 1 and 500')
    params={'api_key':key,'frequency':frequency,'data[0]':data_field,'length':int(length),'sort[0][column]':'period','sort[0][direction]':'desc'}
    if facet_name or facet_value:
        if not facet_name or not facet_value or not re.fullmatch(r'[A-Za-z0-9_-]+',facet_name): raise ValueError('facet_name and facet_value must be supplied together')
        params[f'facets[{facet_name}][]']=facet_value
    if start: params['start']=start
    if end: params['end']=end
    endpoint=f'https://api.eia.gov/v2/{route}/data/?{urlencode(params)}'; payload=_request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'eia-electricity-v2','mode':'AUTH_REQUIRED','configuration_required':False,'data':payload,'provenance':{'organization':'U.S. Energy Information Administration','endpoint':endpoint.replace(key,'[redacted]'),'retrieved_at':_now()},'boundary':NEW_CONNECTORS[1]['boundary']}

def ember_electricity(settings, *, dataset:str='electricity-generation', resolution:str='monthly', entity_code:str, start_date:str='', end_date:str='', limit:int=500):
    key=_setting(settings,'ember_api_key')
    if not key: return {'ok':False,'version':VERSION,'connector_id':'ember-electricity-v1','mode':'AUTH_REQUIRED','configuration_required':True,'configuration_key':'SC_SI_EMBER_API_KEY','network_calls_performed':False}
    if dataset not in {'electricity-generation','electricity-demand','power-sector-emissions','carbon-intensity','installed-capacity'}: raise ValueError('unsupported Ember dataset')
    if resolution not in {'monthly','yearly'}: raise ValueError('resolution must be monthly or yearly')
    code=(entity_code or '').strip().upper()
    if not re.fullmatch(r'[A-Z0-9_-]{2,12}',code): raise ValueError('entity_code is invalid')
    params={'entity_code':code,'api_key':key}
    if start_date: params['start_date']=start_date
    if end_date: params['end_date']=end_date
    endpoint=f'https://api.ember-energy.org/v1/{dataset}/{resolution}?{urlencode(params)}'; payload=_request_json(endpoint,timeout=_timeout(settings))
    rows=payload if isinstance(payload,list) else payload.get('data',[]) if isinstance(payload,dict) else []
    if len(rows)>int(limit): rows=rows[:int(limit)]
    return {'ok':True,'version':VERSION,'connector_id':'ember-electricity-v1','mode':'AUTH_REQUIRED','configuration_required':False,'record_count':len(rows),'data':rows,'provenance':{'organization':'Ember','endpoint':endpoint.replace(key,'[redacted]'),'retrieved_at':_now()},'boundary':NEW_CONNECTORS[2]['boundary']}

def entsoe_data(settings, *, document_type:str, period_start:str, period_end:str, domain_param:str, domain_code:str, process_type:str=''):
    token=_setting(settings,'entsoe_security_token')
    if not token: return {'ok':False,'version':VERSION,'connector_id':'entsoe-transparency-web-api','mode':'AUTH_REQUIRED','configuration_required':True,'configuration_key':'SC_SI_ENTSOE_SECURITY_TOKEN','network_calls_performed':False}
    if not re.fullmatch(r'A\d{2}',document_type or ''): raise ValueError('document_type is invalid')
    if domain_param not in {'in_Domain','out_Domain','inBiddingZone_Domain','outBiddingZone_Domain'}: raise ValueError('domain_param is invalid')
    if not re.fullmatch(r'[A-Za-z0-9-]{10,20}',domain_code or ''): raise ValueError('domain_code is invalid')
    if not (re.fullmatch(r'\d{12}',period_start or '') and re.fullmatch(r'\d{12}',period_end or '')): raise ValueError('periods must be YYYYMMDDHHMM')
    params={'securityToken':token,'documentType':document_type,'periodStart':period_start,'periodEnd':period_end,domain_param:domain_code}
    if process_type: params['processType']=process_type
    endpoint=f'https://web-api.tp.entsoe.eu/api?{urlencode(params)}'; xml=_request_text(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'entsoe-transparency-web-api','mode':'AUTH_REQUIRED','configuration_required':False,'content_type':'application/xml','payload':xml,'provenance':{'organization':'ENTSO-E','endpoint':endpoint.replace(token,'[redacted]'),'retrieved_at':_now()},'boundary':NEW_CONNECTORS[3]['boundary']}

def mlab_locate(settings):
    endpoint='https://locate.measurementlab.net/v2/nearest/ndt/ndt7'; payload=_request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'mlab-locate-v2','mode':'DISCOVERY','data':payload,'provenance':{'organization':'Measurement Lab','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[5]['boundary']}

def fcc_bdc_asofs(settings):
    endpoint='https://broadbandmap.fcc.gov/api/public/map/listAsOfs'; payload=_request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'fcc-bdc-public-data','mode':'DISCOVERY','data':payload,'provenance':{'organization':'U.S. Federal Communications Commission','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[6]['boundary']}
