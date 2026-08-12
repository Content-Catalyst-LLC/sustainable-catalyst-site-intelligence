from __future__ import annotations
"""v4.35.19 — High-Priority Workspace Connector Closure II: Climate & Atmosphere."""
from datetime import datetime, timezone
import re
from typing import Any
from urllib.parse import urlencode

from .version import APP_VERSION
from . import authoritative_connectors_v43511 as prior
from .authoritative_connectors_v4355 import _request_json

VERSION=APP_VERSION
CONTRACT='high-priority-workspace-connector-closure-ii'

def _now(): return datetime.now(timezone.utc).isoformat()
def _timeout(settings): return int(getattr(settings,'external_request_timeout_seconds',8)) if settings is not None else 8
def _setting(settings,name,default=''):
    v=str(getattr(settings,name,'') or '').strip() if settings is not None else ''
    return v or default

NEW_CONNECTORS=(
 {'id':'epa-airnow-current','title':'EPA AirNow Current Observations','organization':'U.S. EPA AirNow','workspace':'Atmosphere, Air Quality & Aerosols','mode':'AUTH_REQUIRED','authentication':'SC_SI_AIRNOW_API_KEY','boundary':'AirNow observations are preliminary public-reporting/forecasting data. They are not regulatory AQS records, a medical recommendation, or a Site Intelligence-issued advisory.'},
 {'id':'ecmwf-era5-catalogue','title':'Copernicus Climate Data Store ERA5 Catalogue','organization':'Copernicus Climate Change Service / ECMWF','workspace':'Climate Baselines, Anomalies & Extremes','mode':'DISCOVERY','authentication':'public','boundary':'Catalogue metadata establishes dataset availability and characteristics, not a direct observation at a point. ERA5 is reanalysis; authenticated CDS retrieval is a separate operation and ERA5T may later change.'},
 {'id':'ecmwf-cams-catalogue','title':'Copernicus Atmosphere Data Store CAMS Catalogue','organization':'Copernicus Atmosphere Monitoring Service / ECMWF','workspace':'Atmosphere, Air Quality & Aerosols','mode':'DISCOVERY','authentication':'public','boundary':'Catalogue metadata identifies CAMS model/analysis/forecast products. It is not ground-monitor evidence, a regulatory determination, or a surface-exposure measurement.'},
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
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'connector_count':len(rows),'live_connector_count':sum(x['mode']=='LIVE' for x in rows),'discovery_connector_count':sum(x['mode']=='DISCOVERY' for x in rows),'auth_required_connector_count':sum(x['mode']=='AUTH_REQUIRED' for x in rows),'configured_auth_required_connector_count':sum(x['mode']=='AUTH_REQUIRED' and x.get('credential_configured') for x in rows),'closure_ii_connector_count':3,'connectors':rows,'principles':['Climate and Atmosphere REGISTERED backlog closure is distinct from credential completion.','AirNow preliminary observations remain semantically separate from regulatory AQS data.','ERA5 and CAMS catalogue APIs are DISCOVERY; catalogue presence is never promoted to an observation.','Upstream availability remains non-blocking for deployment.'],'generated_at':_now()}

def connector_readiness(settings=None):
    c=connector_catalog(settings); ids={x['id'] for x in c['connectors']}; expected={x['id'] for x in NEW_CONNECTORS}
    checks={'thirty_five_interfaces_registered':c['connector_count']==35,'twenty_three_live':c['live_connector_count']==23,'six_discovery':c['discovery_connector_count']==6,'six_auth_required':c['auth_required_connector_count']==6,'closure_ii_ids_present':expected.issubset(ids),'network_free':True,'upstream_health_non_blocking':True}
    return {'ok':all(checks.values()),'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'checks':checks,'generated_at':_now()}

def airnow_current(settings, *, latitude:float, longitude:float, distance_miles:int=25):
    key=_setting(settings,'airnow_api_key')
    if not key:
        return {'ok':False,'version':VERSION,'connector_id':'epa-airnow-current','mode':'AUTH_REQUIRED','configuration_required':True,'configuration_key':'SC_SI_AIRNOW_API_KEY','network_calls_performed':False,'boundary':NEW_CONNECTORS[0]['boundary']}
    lat=float(latitude); lon=float(longitude); distance=int(distance_miles)
    if not -90<=lat<=90 or not -180<=lon<=180: raise ValueError('latitude/longitude are out of bounds')
    if not 1<=distance<=250: raise ValueError('distance_miles must be between 1 and 250')
    base=_setting(settings,'airnow_base_url','https://www.airnowapi.org/aq').rstrip('/')
    params={'format':'application/json','latitude':lat,'longitude':lon,'distance':distance,'API_KEY':key}
    endpoint=f"{base}/observation/latLong/current/?{urlencode(params)}"
    payload=_request_json(endpoint,timeout=_timeout(settings))
    rows=payload if isinstance(payload,list) else []
    clean=[]
    for row in rows[:50]:
        if not isinstance(row,dict): continue
        clean.append({k:row.get(k) for k in ('DateObserved','HourObserved','LocalTimeZone','ReportingArea','StateCode','Latitude','Longitude','ParameterName','AQI','Category')})
    return {'ok':True,'version':VERSION,'connector_id':'epa-airnow-current','mode':'AUTH_REQUIRED','configuration_required':False,'query':{'latitude':lat,'longitude':lon,'distance_miles':distance},'record_count':len(clean),'data':clean,'provenance':{'organization':'U.S. EPA AirNow','endpoint':endpoint.replace(key,'[redacted]'),'retrieved_at':_now(),'data_status':'preliminary-subject-to-change'},'boundary':NEW_CONNECTORS[0]['boundary']}

def _collection(settings, *, store:str, collection_id:str, connector_id:str, organization:str, boundary:str):
    if store not in {'cds','ads'}: raise ValueError('store must be cds or ads')
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{2,120}',collection_id or ''): raise ValueError('collection_id is invalid')
    setting='ecmwf_cds_catalogue_base_url' if store=='cds' else 'ecmwf_ads_catalogue_base_url'
    default='https://cds.climate.copernicus.eu/api/catalogue/v1' if store=='cds' else 'https://ads.atmosphere.copernicus.eu/api/catalogue/v1'
    base=_setting(settings,setting,default).rstrip('/')
    endpoint=f'{base}/collections/{collection_id}'
    payload=_request_json(endpoint,timeout=_timeout(settings))
    keep={k:payload.get(k) for k in ('id','title','description','extent','license','providers','keywords','links') if isinstance(payload,dict) and k in payload}
    return {'ok':True,'version':VERSION,'connector_id':connector_id,'mode':'DISCOVERY','collection_id':collection_id,'data':keep,'provenance':{'organization':organization,'endpoint':endpoint,'retrieved_at':_now()},'boundary':boundary}

def era5_catalogue(settings, *, collection_id:str='reanalysis-era5-single-levels'):
    allowed={'reanalysis-era5-single-levels','reanalysis-era5-pressure-levels','derived-era5-single-levels-daily-statistics','derived-era5-pressure-levels-daily-statistics'}
    if collection_id not in allowed: raise ValueError('unsupported bounded ERA5 collection')
    return _collection(settings,store='cds',collection_id=collection_id,connector_id='ecmwf-era5-catalogue',organization='Copernicus Climate Change Service / ECMWF',boundary=NEW_CONNECTORS[1]['boundary'])

def cams_catalogue(settings, *, collection_id:str='cams-global-atmospheric-composition-forecasts'):
    allowed={'cams-global-atmospheric-composition-forecasts','cams-global-reanalysis-eac4','cams-global-reanalysis-eac4-monthly'}
    if collection_id not in allowed: raise ValueError('unsupported bounded CAMS collection')
    return _collection(settings,store='ads',collection_id=collection_id,connector_id='ecmwf-cams-catalogue',organization='Copernicus Atmosphere Monitoring Service / ECMWF',boundary=NEW_CONNECTORS[2]['boundary'])
