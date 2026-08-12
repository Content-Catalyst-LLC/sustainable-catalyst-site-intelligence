from __future__ import annotations
"""v4.35.16 — High-Priority Workspace Connector Closure V: Mining, Critical Materials & Industrial Systems."""
from datetime import datetime, timezone
import re
from typing import Any
from urllib.parse import urlencode, quote

from .version import APP_VERSION
from . import authoritative_connectors_v43514 as prior
from .authoritative_connectors_v4355 import _request_json

VERSION=APP_VERSION
CONTRACT='high-priority-workspace-connector-closure-v'

def _now(): return datetime.now(timezone.utc).isoformat()
def _timeout(settings): return int(getattr(settings,'external_request_timeout_seconds',8)) if settings is not None else 8
def _setting(settings,name,default=''):
    v=str(getattr(settings,name,'') or '').strip() if settings is not None else ''
    return v or default

def _point(lat,lon,radius_km):
    lat=float(lat); lon=float(lon); radius=float(radius_km)
    if not -90<=lat<=90 or not -180<=lon<=180 or not 0<radius<=50: raise ValueError('latitude/longitude/radius are out of bounds')
    return lat,lon,radius

def _overpass_multi(settings,lat,lon,radius_km,filters,connector_id,boundary):
    lat,lon,radius=_point(lat,lon,radius_km); r=int(round(radius*1000))
    clauses=[]
    for flt in filters:
        if not re.fullmatch(r'[A-Za-z0-9_:.-]+(?:=[A-Za-z0-9_:.-]+)?',flt): raise ValueError('invalid Overpass filter')
        for kind in ('node','way','relation'): clauses.append(f'{kind}(around:{r},{lat},{lon})[{flt}];')
    query='[out:json][timeout:20];('+''.join(clauses)+');out center tags qt 250;'
    base=_setting(settings,'overpass_api_base_url','https://overpass-api.de/api/interpreter')
    endpoint=f'{base}?{urlencode({"data":query})}'; data=_request_json(endpoint,timeout=_timeout(settings))
    elements=(data.get('elements') or []) if isinstance(data,dict) else []
    return {'ok':True,'version':VERSION,'connector_id':connector_id,'mode':'LIVE','query':{'latitude':lat,'longitude':lon,'radius_km':radius},'record_count':len(elements),'data':elements[:250],'provenance':{'organization':'OpenStreetMap contributors / Overpass','endpoint':endpoint,'retrieved_at':_now()},'boundary':boundary}

NEW_CONNECTORS=(
 {'id':'osm-mining-overpass','title':'OpenStreetMap Mining & Quarry Features via Overpass','organization':'OpenStreetMap contributors / Overpass','workspace':'Mining & Critical Materials','mode':'LIVE','authentication':'public','boundary':'Community-mapped extraction features are supplemental. They do not establish ownership, active operation, production, reserves, permit status, environmental compliance, worker safety or legal access.'},
 {'id':'usgs-usmin-sdc','title':'USGS USMIN / Science Data Catalog Metadata API','organization':'U.S. Geological Survey','workspace':'Mining & Critical Materials','mode':'DISCOVERY','authentication':'public','boundary':'USMIN metadata/data-release discovery describes mineral deposits and related geospatial products; it is not live mine operations, reserve certification, economic recoverability or permit status.'},
 {'id':'usgs-mcs-2026-sdc','title':'USGS Mineral Commodity Summaries 2026 Data Release API','organization':'U.S. Geological Survey National Minerals Information Center','workspace':'Mining & Critical Materials','mode':'DISCOVERY','authentication':'public','boundary':'MCS 2026 data-release metadata and downloadable statistics are annual compiled estimates for 2021–2025. They are not mine-level telemetry, current inventories, guaranteed reserves, forecasts or disruption findings.'},
 {'id':'osm-industrial-overpass','title':'OpenStreetMap Industrial Facilities via Overpass','organization':'OpenStreetMap contributors / Overpass','workspace':'Industrial Manufacturing & Trade','mode':'LIVE','authentication':'public','boundary':'Community-mapped industrial geometry is supplemental and does not establish ownership, current operation, production volume, employment, regulatory status, hazardous-material inventory or legal access.'},
 {'id':'world-bank-wits-trade-stats','title':'World Bank WITS Trade Stats REST API','organization':'World Bank','workspace':'Industrial Manufacturing & Trade','mode':'LIVE','authentication':'public','boundary':'WITS Trade Stats are reported/aggregated customs and statistical records, not shipment telemetry. Reporter/partner asymmetry, classification, valuation, timing and re-export effects remain visible; bilateral trade does not prove dependency, origin content or inventory.'},
)
CONNECTORS=tuple(prior.CONNECTORS)+NEW_CONNECTORS
for _name in [n for n in dir(prior) if not n.startswith('_') and callable(getattr(prior,n)) and n not in {'connector_catalog','connector_readiness'}]:
    if _name not in globals(): globals()[_name]=getattr(prior,_name)

def connector_catalog(settings=None):
    rows=[dict(x) for x in prior.connector_catalog(settings)['connectors']]
    for c in NEW_CONNECTORS:
        r=dict(c); r.update({'credential_configured':True,'configuration_key':None,'network_check_performed':False}); rows.append(r)
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'connector_count':len(rows),'live_connector_count':sum(x['mode']=='LIVE' for x in rows),'discovery_connector_count':sum(x['mode']=='DISCOVERY' for x in rows),'auth_required_connector_count':sum(x['mode']=='AUTH_REQUIRED' for x in rows),'configured_auth_required_connector_count':sum(x['mode']=='AUTH_REQUIRED' and x.get('credential_configured') for x in rows),'closure_v_connector_count':5,'connectors':rows,'principles':['Mining/Critical Materials and Industrial Manufacturing/Trade have zero ambiguous REGISTERED machine-interface backlog after closure V.','USGS SDC/ScienceBase metadata interfaces are DISCOVERY; metadata presence is not a mine observation or commodity statistic.','OSM facilities remain supplemental community mapping evidence.','WITS trade statistics remain distinct from physical shipment telemetry and causal supply-chain claims.','Upstream availability remains non-blocking for deployment.'],'generated_at':_now()}

def connector_readiness(settings=None):
    c=connector_catalog(settings); ids={x['id'] for x in c['connectors']}; expected={x['id'] for x in NEW_CONNECTORS}
    checks={'fifty_interfaces_registered':c['connector_count']==50,'thirty_one_live':c['live_connector_count']==31,'eleven_discovery':c['discovery_connector_count']==11,'eight_auth_required':c['auth_required_connector_count']==8,'closure_v_ids_present':expected.issubset(ids),'network_free':True,'upstream_health_non_blocking':True}
    return {'ok':all(checks.values()),'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'checks':checks,'generated_at':_now()}

def osm_mining(settings, *, latitude:float, longitude:float, radius_km:float=10):
    return _overpass_multi(settings,latitude,longitude,radius_km,('landuse=quarry','man_made=mineshaft','man_made=adit','industrial=mine'),'osm-mining-overpass',NEW_CONNECTORS[0]['boundary'])

def usgs_usmin_discovery(settings, *, record_id:str='USGS:6464de5bd34ec179a83d9e6c'):
    if not re.fullmatch(r'USGS:[A-Za-z0-9]+',record_id or ''): raise ValueError('record_id must be a USGS Science Data Catalog identifier')
    base=_setting(settings,'usgs_sdc_api_base_url','https://data.usgs.gov/datacatalog/api').rstrip('/')
    endpoint=f'{base}/search/{quote(record_id,safe="")}'
    payload=_request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'usgs-usmin-sdc','mode':'DISCOVERY','record_id':record_id,'data':payload,'provenance':{'organization':'U.S. Geological Survey','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[1]['boundary']}

def usgs_mcs_2026_discovery(settings, *, record_id:str='USGS:69837e43b66b01367d7ec7c7'):
    if not re.fullmatch(r'USGS:[A-Za-z0-9]+',record_id or ''): raise ValueError('record_id must be a USGS Science Data Catalog identifier')
    base=_setting(settings,'usgs_sdc_api_base_url','https://data.usgs.gov/datacatalog/api').rstrip('/')
    endpoint=f'{base}/search/{quote(record_id,safe="")}'
    payload=_request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'usgs-mcs-2026-sdc','mode':'DISCOVERY','record_id':record_id,'data':payload,'provenance':{'organization':'U.S. Geological Survey National Minerals Information Center','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[2]['boundary']}

def osm_industrial(settings, *, latitude:float, longitude:float, radius_km:float=10):
    return _overpass_multi(settings,latitude,longitude,radius_km,('landuse=industrial','man_made=works','industrial=refinery','building=warehouse'),'osm-industrial-overpass',NEW_CONNECTORS[3]['boundary'])

def wits_trade_stats(settings, *, reporter:str, year:int, partner:str='wld', product:str='999999', indicator:str='XPRT-TRD-VL', dataset:str='tradestats-trade'):
    dataset=(dataset or '').strip().lower()
    if dataset not in {'tradestats-trade','tradestats-tariff','tradestats-development'}: raise ValueError('unsupported WITS dataset')
    reporter=(reporter or '').strip().lower(); partner=(partner or '').strip().lower(); product=(product or '').strip().lower(); indicator=(indicator or '').strip().upper()
    if reporter=='all' or not re.fullmatch(r'[a-z0-9]{3}',reporter): raise ValueError('reporter must be a specific three-character WITS code')
    if not 1988<=int(year)<=2100: raise ValueError('year must be 1988 or later')
    if partner!='all' and not re.fullmatch(r'[a-z0-9]{3}',partner): raise ValueError('partner is invalid')
    if product!='all' and not re.fullmatch(r'[a-z0-9_-]{3,20}',product): raise ValueError('product is invalid')
    if indicator!='ALL' and not re.fullmatch(r'[A-Z0-9-]{3,40}',indicator): raise ValueError('indicator is invalid')
    if dataset=='tradestats-development':
        path=f'datasource/{dataset}/reporter/{reporter}/year/{int(year)}/indicator/{indicator}'
    else:
        if partner=='all' and product=='all' and indicator=='ALL': raise ValueError('WITS query is too broad')
        path=f'datasource/{dataset}/reporter/{reporter}/year/{int(year)}/partner/{partner}/product/{product}/indicator/{indicator}'
    base=_setting(settings,'wits_api_base_url','https://wits.worldbank.org/API/V1/SDMX/V21').rstrip('/')
    endpoint=f'{base}/{path}?format=JSON'; payload=_request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'world-bank-wits-trade-stats','mode':'LIVE','query':{'dataset':dataset,'reporter':reporter,'year':int(year),'partner':partner if dataset!='tradestats-development' else None,'product':product if dataset!='tradestats-development' else None,'indicator':indicator},'data':payload,'provenance':{'organization':'World Bank WITS','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[4]['boundary']}
