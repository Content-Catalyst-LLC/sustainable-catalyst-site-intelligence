from __future__ import annotations
"""v4.35.13 — High-Priority Workspace Connector Closure III: Water, Hydrology & Sanitation."""
from datetime import datetime, timezone
import re
from typing import Any
from urllib.parse import quote, urlencode

from .version import APP_VERSION
from . import authoritative_connectors_v43512 as prior
from .authoritative_connectors_v4355 import _request_json

VERSION=APP_VERSION
CONTRACT='high-priority-workspace-connector-closure-iii'

def _now(): return datetime.now(timezone.utc).isoformat()
def _timeout(settings): return int(getattr(settings,'external_request_timeout_seconds',8)) if settings is not None else 8
def _setting(settings,name,default=''):
    v=str(getattr(settings,name,'') or '').strip() if settings is not None else ''
    return v or default

NEW_CONNECTORS=(
 {'id':'osm-water-overpass','title':'OpenStreetMap Water & Wastewater Infrastructure via Overpass','organization':'OpenStreetMap contributors / Overpass','workspace':'Water, Wastewater & Sanitation','mode':'LIVE','authentication':'public','boundary':'Community-mapped water infrastructure is supplemental. A mapped feature does not establish operation, capacity, ownership, water safety, service territory, discharge compliance or legal access.'},
 {'id':'epa-sdwis-envirofacts','title':'EPA SDWIS via Envirofacts Data Service','organization':'U.S. Environmental Protection Agency','workspace':'Water, Wastewater & Sanitation','mode':'LIVE','authentication':'public','boundary':'SDWIS/Envirofacts records are administrative and regulatory records. They are not real-time tap-water telemetry, household service confirmation, or a new Site Intelligence compliance/safety determination.'},
 {'id':'noaa-nidis-drought-json','title':'NOAA NIDIS / Drought.gov Public JSON & GeoJSON','organization':'NOAA National Integrated Drought Information System','workspace':'Hydrology, Rivers, Flood & Drought','mode':'LIVE','authentication':'public','boundary':'Drought.gov files retain source product definitions, valid dates and methods. Site Intelligence does not synthesize them into an independent drought declaration, flood warning, or emergency determination.'},
 {'id':'nasa-gpm-imerg-cmr','title':'NASA GPM IMERG via EOSDIS CMR Discovery','organization':'NASA GES DISC / EOSDIS','workspace':'Hydrology, Rivers, Flood & Drought','mode':'DISCOVERY','authentication':'public discovery; Earthdata login may be required for scientific file retrieval','boundary':'CMR results are metadata/discovery records for GPM/IMERG collections, not precipitation observations. Satellite precipitation estimates remain distinct from rain-gauge measurements.'},
 {'id':'copernicus-glofas-layers','title':'Copernicus GloFAS Public Product-Layer API','organization':'Copernicus Emergency Management Service / ECMWF','workspace':'Hydrology, Rivers, Flood & Drought','mode':'DISCOVERY','authentication':'public layer discovery; EWDS/API credentials may be required for data retrieval','boundary':'GloFAS is modeled hydrological/flood-awareness evidence. Public layer availability is discovery, not a local gauge observation or official local flood warning; EWDS is not a time-critical operational service.'},
)
CONNECTORS=tuple(prior.CONNECTORS)+NEW_CONNECTORS
for _name in [n for n in dir(prior) if not n.startswith('_') and callable(getattr(prior,n)) and n not in {'connector_catalog','connector_readiness'}]:
    if _name not in globals(): globals()[_name]=getattr(prior,_name)

def connector_catalog(settings=None):
    rows=[dict(x) for x in prior.connector_catalog(settings)['connectors']]
    for c in NEW_CONNECTORS:
        r=dict(c); r.update({'credential_configured':True,'configuration_key':None,'network_check_performed':False}); rows.append(r)
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'connector_count':len(rows),'live_connector_count':sum(x['mode']=='LIVE' for x in rows),'discovery_connector_count':sum(x['mode']=='DISCOVERY' for x in rows),'auth_required_connector_count':sum(x['mode']=='AUTH_REQUIRED' for x in rows),'configured_auth_required_connector_count':sum(x['mode']=='AUTH_REQUIRED' and x.get('credential_configured') for x in rows),'closure_iii_connector_count':5,'connectors':rows,'principles':['Water, Hydrology and Sanitation REGISTERED backlog closure is distinct from complete global data coverage.','Community-mapped infrastructure remains supplemental evidence.','SDWIS administrative/regulatory records are not real-time tap-water safety telemetry.','NASA GPM CMR and GloFAS public-layer interfaces are DISCOVERY and are never promoted to observations.','Upstream availability remains non-blocking for deployment.'],'generated_at':_now()}

def connector_readiness(settings=None):
    c=connector_catalog(settings); ids={x['id'] for x in c['connectors']}; expected={x['id'] for x in NEW_CONNECTORS}
    checks={'forty_interfaces_registered':c['connector_count']==40,'twenty_six_live':c['live_connector_count']==26,'eight_discovery':c['discovery_connector_count']==8,'six_auth_required':c['auth_required_connector_count']==6,'closure_iii_ids_present':expected.issubset(ids),'network_free':True,'upstream_health_non_blocking':True}
    return {'ok':all(checks.values()),'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'checks':checks,'generated_at':_now()}

def _point(lat,lon,radius_km):
    lat=float(lat); lon=float(lon); radius=float(radius_km)
    if not -90<=lat<=90 or not -180<=lon<=180 or not 0<radius<=50: raise ValueError('latitude/longitude/radius are out of bounds')
    return lat,lon,radius

def osm_water(settings, *, latitude:float, longitude:float, radius_km:float=10):
    lat,lon,radius=_point(latitude,longitude,radius_km); meters=int(round(radius*1000))
    selector='man_made~"water_works|wastewater_plant|water_tower|pumping_station|reservoir_covered"'
    query=f'[out:json][timeout:20];(node(around:{meters},{lat},{lon})[{selector}];way(around:{meters},{lat},{lon})[{selector}];relation(around:{meters},{lat},{lon})[{selector}];);out center tags qt 250;'
    base=_setting(settings,'overpass_api_base_url','https://overpass-api.de/api/interpreter')
    endpoint=f'{base}?{urlencode({"data":query})}'
    data=_request_json(endpoint,timeout=_timeout(settings)); elements=(data.get('elements') or []) if isinstance(data,dict) else []
    return {'ok':True,'version':VERSION,'connector_id':'osm-water-overpass','mode':'LIVE','query':{'latitude':lat,'longitude':lon,'radius_km':radius},'record_count':len(elements),'data':elements[:250],'provenance':{'organization':'OpenStreetMap contributors / Overpass','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[0]['boundary']}

_SDWIS_TABLES={
 'county-served':('SDW_COUNTY_SERVED',{'STATE','COUNTYSERVED','PWSID'}),
 'violations-enforcement':('SDW_VIOL_ENFORCEMENT',{'STATE','PWSID','COUNTYSERVED'}),
 'geographic-area':('GEOGRAPHIC_AREA',{'STATE_SERVED','COUNTY_SERVED','PWSID','ZIP_CODE_SERVED'}),
 'water-system':('WATER_SYSTEM',{'PWSID','PRIMACY_AGENCY_CODE','EPA_REGION'}),
}
def epa_sdwis(settings, *, dataset:str='county-served', filter_column:str='', filter_value:str='', limit:int=100):
    if dataset not in _SDWIS_TABLES: raise ValueError('unsupported SDWIS dataset')
    table,columns=_SDWIS_TABLES[dataset]; limit=int(limit)
    if not 1<=limit<=500: raise ValueError('limit must be between 1 and 500')
    if bool(filter_column)!=bool(filter_value): raise ValueError('filter_column and filter_value must be supplied together')
    path=f'{table}/ROWS/0:{limit}'
    if filter_column:
        col=filter_column.strip().upper(); val=filter_value.strip()
        if col not in columns: raise ValueError('filter_column is not allowlisted for this SDWIS dataset')
        if not re.fullmatch(r'[A-Za-z0-9 .,_()/-]{1,80}',val): raise ValueError('filter_value contains unsupported characters')
        path=f'{table}/{col}/{quote(val,safe="")}/ROWS/0:{limit}'
    base=_setting(settings,'epa_envirofacts_base_url','https://data.epa.gov/efservice').rstrip('/')
    endpoint=f'{base}/{path}/JSON'
    payload=_request_json(endpoint,timeout=_timeout(settings)); rows=payload if isinstance(payload,list) else payload.get('results',[]) if isinstance(payload,dict) else []
    if not isinstance(rows,list): rows=[]
    return {'ok':True,'version':VERSION,'connector_id':'epa-sdwis-envirofacts','mode':'LIVE','query':{'dataset':dataset,'filter_column':filter_column or None,'filter_value':filter_value or None,'limit':limit},'record_count':len(rows[:limit]),'data':rows[:limit],'provenance':{'organization':'U.S. Environmental Protection Agency','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[1]['boundary']}

def nidis_drought_file(settings, *, relative_path:str):
    p=(relative_path or '').strip().lstrip('/')
    if not p or len(p)>220 or '..' in p or not re.fullmatch(r'[A-Za-z0-9_./-]+\.(json|geojson|topojson)',p,re.I): raise ValueError('relative_path must be a bounded JSON/GeoJSON/TopoJSON object path')
    base=_setting(settings,'nidis_public_json_base_url','https://storage.googleapis.com/noaa-nidis-drought-gov-data/current-conditions/json/v1').rstrip('/')
    endpoint=f'{base}/{p}'
    payload=_request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'noaa-nidis-drought-json','mode':'LIVE','query':{'relative_path':p},'data':payload,'provenance':{'organization':'NOAA National Integrated Drought Information System','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[2]['boundary']}

def nasa_gpm_imerg_discovery(settings, *, limit:int=20, temporal:str='', bounding_box:str=''):
    result=prior.nasa_cmr_collections(settings,query='GPM IMERG',limit=limit,provider='GES_DISC',temporal=temporal,bounding_box=bounding_box)
    result=dict(result); result.update({'version':VERSION,'connector_id':'nasa-gpm-imerg-cmr','source':'NASA GES DISC / EOSDIS CMR','boundary':NEW_CONNECTORS[3]['boundary']})
    return result

def glofas_layers(settings):
    endpoint=_setting(settings,'glofas_layers_url','https://european-flood.emergency.copernicus.eu/api/fms/download/glofas/')
    payload=_request_json(endpoint,timeout=_timeout(settings)); supported=(payload.get('supported_layers') or []) if isinstance(payload,dict) else []
    if not isinstance(supported,list): supported=[]
    clean=[]
    for row in supported[:200]:
        if isinstance(row,dict): clean.append({k:row.get(k) for k in ('name','url') if k in row})
    return {'ok':True,'version':VERSION,'connector_id':'copernicus-glofas-layers','mode':'DISCOVERY','layer_count':len(clean),'layers':clean,'provenance':{'organization':'Copernicus Emergency Management Service / ECMWF','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[4]['boundary']}
