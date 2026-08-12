from __future__ import annotations

"""Site Intelligence v4.35.14 — Authoritative Connector Expansion IV.

Adds bounded first-party connectors for FAOSTAT, ILOSTAT, OECD Data Explorer
SDMX, U.S. EPA Facility Registry Service, and USGS Volcano HANS.  Readiness is
network-free and upstream health remains non-blocking for release promotion.
"""
from datetime import datetime, timezone
import re
from typing import Any
from urllib.parse import urlencode, quote

from .version import APP_VERSION
from . import authoritative_connectors_v4356 as prior
from . import authoritative_connectors_v4355 as shared

VERSION=APP_VERSION
CONTRACT='authoritative-connector-expansion-iv'

NEW_CONNECTORS=(
    {"id":"faostat-data-api","title":"FAOSTAT Data API","organization":"Food and Agriculture Organization of the United Nations","workspace":"Agriculture / Food Security / Human Development","mode":"LIVE","protocol":"REST / JSON / CSV","base_url_setting":"faostat_api_base_url","authentication":"Public data API; base URL is server-configurable.","boundary":"FAOSTAT statistical observations retain domain, area, item, element, year, unit, flags and notes. They are not real-time crop or food-security conditions."},
    {"id":"ilostat-sdmx","title":"ILOSTAT SDMX / indicator service","organization":"International Labour Organization","workspace":"Human Development / Economics / Labor","mode":"LIVE","protocol":"SDMX / REST / JSON","base_url_setting":"ilostat_api_base_url","authentication":"Public statistical service.","boundary":"National survey observations, harmonized series and ILO modelled estimates remain explicitly distinguished; seasonal adjustment and source type are not silently collapsed."},
    {"id":"oecd-data-explorer-sdmx","title":"OECD Data Explorer SDMX API","organization":"OECD","workspace":"Economics / Development / Environment","mode":"LIVE","protocol":"SDMX REST / JSON / CSV","base_url_setting":"oecd_sdmx_base_url","authentication":"Public API subject to OECD rate limits.","boundary":"Dataset agency, dataflow, version, SDMX key, frequency, unit and observation attributes remain part of the evidence record."},
    {"id":"epa-frs-public-api","title":"EPA Facility Registry Service API","organization":"U.S. Environmental Protection Agency","workspace":"Industrial Manufacturing & Trade / Facilities","mode":"LIVE","protocol":"REST / JSON","base_url_setting":"epa_frs_base_url","authentication":"Public query-only API.","boundary":"FRS provides facility identity and program linkage; inclusion is not itself a compliance violation, emissions measurement, exposure finding or legal conclusion."},
    {"id":"usgs-volcano-hans","title":"USGS Volcano Hazards Program HANS","organization":"U.S. Geological Survey Volcano Hazards Program","workspace":"Geosphere / Volcanoes","mode":"LIVE","protocol":"REST / JSON","base_url_setting":"usgs_volcano_hans_base_url","authentication":"Public machine service; USGS notes application-support interfaces may change.","boundary":"USGS notices and alert/color codes are authoritative source statements. Site Intelligence does not create, escalate, downgrade or supersede volcano alerts."},
)
CONNECTORS=tuple(prior.CONNECTORS)+NEW_CONNECTORS

# Preserve all prior public clients.
for _name in (
'usgs_water_latest','noaa_erddap_search','noaa_erddap_tabledap','nasa_exoplanet_planets','unhcr_population','nasa_cmr_collections',
'noaa_coops_data','ncei_access_data','obis_occurrences','eurostat_statistics','usda_soil_mapunits','usfws_nwi_wetlands','epa_echo_facilities',
'nasa_firms_area','usda_nass_quickstats','nasa_cmr_graphql_collections','pcbs_pxweb_metadata','pcbs_pxweb_data','statcan_vectors','ons_observations','abs_sdmx_data','bls_timeseries'):
    globals()[_name]=getattr(prior,_name)

def _now(): return datetime.now(timezone.utc).isoformat()
def _setting(settings,name,default):
    value=str(getattr(settings,name,'') or '').strip() if settings is not None else ''
    return value or default
def _timeout(settings): return int(getattr(settings,'external_request_timeout_seconds',8)) if settings is not None else 8

def _default_base(cid):
    return {
        'faostat-data-api':'https://fenixservices.fao.org/faostat/api/v1',
        'ilostat-sdmx':'https://rplumber.ilo.org/data/indicator',
        'oecd-data-explorer-sdmx':'https://sdmx.oecd.org/public/rest',
        'epa-frs-public-api':'https://ofmpub.epa.gov/frs_public2/frs_rest_services.get_facilities',
        'usgs-volcano-hans':'https://volcanoes.usgs.gov/vsc/api/hansApi',
    }[cid]

def connector_catalog(settings=None):
    base=prior.connector_catalog(settings); rows=[dict(x) for x in base['connectors']]
    for c in NEW_CONNECTORS:
        r=dict(c); r['configured_base_url']=_setting(settings,c['base_url_setting'],_default_base(c['id'])); r['credential_configured']=True; r['network_check_performed']=False; rows.append(r)
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'connector_count':len(rows),'live_connector_count':sum(x['mode']=='LIVE' for x in rows),'discovery_connector_count':sum(x['mode']=='DISCOVERY' for x in rows),'auth_required_connector_count':sum(x['mode']=='AUTH_REQUIRED' for x in rows),'configured_auth_required_connector_count':sum(x['mode']=='AUTH_REQUIRED' and x.get('credential_configured') for x in rows),'expansion_iv_connector_count':5,'connectors':rows,'principles':list(base.get('principles') or [])+['Expansion IV connects first-party statistical, facility-identity and volcano-notification services with bounded public queries.','Upstream source health remains operational telemetry and never a release blocker.'],'generated_at':_now()}

def connector_readiness(settings=None):
    c=connector_catalog(settings); ids={x['id'] for x in c['connectors']}; expected={x['id'] for x in NEW_CONNECTORS}
    checks={'twenty_five_authoritative_interfaces_registered':c['connector_count']==25,'twenty_one_public_live_connectors':c['live_connector_count']==21,'two_discovery_connectors':c['discovery_connector_count']==2,'two_credential_gated_connectors':c['auth_required_connector_count']==2,'expansion_iv_five_ids_present':expected.issubset(ids),'network_checks_not_required_for_deterministic_readiness':True,'release_gate_does_not_depend_on_upstream_health':True}
    return {'ok':all(checks.values()),'version':VERSION,'contract':CONTRACT,'network_calls_performed':False,'checks':checks,'generated_at':_now()}

def _code(value,name,maxlen=32):
    v=(value or '').strip()
    if not v or len(v)>maxlen or not re.fullmatch(r'[A-Za-z0-9_.@-]+',v): raise ValueError(f'{name} is invalid')
    return v

def faostat_data(settings, *, domain:str, area:str='', item:str='', element:str='', year:str='', limit:int=250):
    dom=_code(domain,'domain',12)
    if not 1<=int(limit)<=1000: raise ValueError('limit must be between 1 and 1000')
    params={'page_size':int(limit),'output_type':'objects','show_codes':'true','show_unit':'true','show_flags':'true','show_notes':'true'}
    for k,v in [('area',area),('item',item),('element',element),('year',year)]:
        if v:
            parts=[p.strip() for p in v.split(',') if p.strip()]
            if len(parts)>20 or any(len(p)>40 or not re.fullmatch(r'[A-Za-z0-9_.-]+',p) for p in parts): raise ValueError(f'{k} filter is invalid')
            params[k]=','.join(parts)
    if not any(k in params for k in ('area','item','element','year')): raise ValueError('FAOSTAT public queries require at least one bounded dimension filter')
    base=_setting(settings,'faostat_api_base_url',_default_base('faostat-data-api')).rstrip('/')
    endpoint=f"{base}/en/data/{quote(dom)}?{urlencode(params)}"
    data=shared._request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'faostat-data-api','mode':'LIVE','domain':dom,'data':data,'provenance':{'organization':'Food and Agriculture Organization of the United Nations','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[0]['boundary']}

def ilostat_indicator(settings, *, indicator:str, ref_area:str, start_year:int|None=None, end_year:int|None=None):
    ind=_code(indicator,'indicator',64); area=_code(ref_area,'ref_area',8).upper()
    params={'id':ind,'ref_area':area}
    if start_year is not None or end_year is not None:
        sy=int(start_year or end_year); ey=int(end_year or start_year)
        if sy<1950 or ey>2100 or sy>ey or ey-sy>30: raise ValueError('ILOSTAT year range must be ordered and at most 30 years')
        params.update({'timefrom':sy,'timeto':ey})
    base=_setting(settings,'ilostat_api_base_url',_default_base('ilostat-sdmx')).rstrip('/')
    endpoint=f"{base}?{urlencode(params)}"; data=shared._request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'ilostat-sdmx','mode':'LIVE','indicator':ind,'ref_area':area,'data':data,'provenance':{'organization':'International Labour Organization','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[1]['boundary']}

def oecd_sdmx_data(settings, *, agency:str, dataflow:str, version:str='', key:str='', start_period:str='', end_period:str=''):
    agency_v=_code(agency,'agency',80); flow=_code(dataflow,'dataflow',120); ver=(version or '').strip(); key_v=(key or '').strip()
    if key_v in {'','all','*'}: raise ValueError('OECD public connector requires an explicit bounded SDMX key')
    if len(key_v)>300 or not re.fullmatch(r'[A-Za-z0-9+._-]+',key_v): raise ValueError('key is invalid')
    ident=f'{agency_v},{flow}' + (f',{_code(ver,"version",32)}' if ver else ',')
    params={'dimensionAtObservation':'AllDimensions','format':'csvfilewithlabels'}
    if start_period: params['startPeriod']=start_period
    if end_period: params['endPeriod']=end_period
    base=_setting(settings,'oecd_sdmx_base_url',_default_base('oecd-data-explorer-sdmx')).rstrip('/')
    endpoint=f"{base}/data/{quote(ident,safe=',@')}/{quote(key_v,safe='.+')}?{urlencode(params)}"
    rows=shared._request_csv(endpoint,timeout=_timeout(settings))
    if len(rows)>5000: raise ValueError('OECD response exceeds the 5,000-row Site Intelligence public bound')
    return {'ok':True,'version':VERSION,'connector_id':'oecd-data-explorer-sdmx','mode':'LIVE','row_count':len(rows),'data':rows,'provenance':{'organization':'OECD','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[2]['boundary']}

def epa_frs_facilities(settings, *, registry_id:str='', facility_name:str='', state_abbr:str='', city_name:str='', zip_code:str='', program_acronym:str='', latitude:float|None=None, longitude:float|None=None, search_radius:float|None=None):
    params={'output':'JSON'}
    if registry_id: params['registry_id']=_code(registry_id,'registry_id',20)
    if facility_name:
        if len(facility_name.strip())<3 or len(facility_name)>100: raise ValueError('facility_name must be 3-100 characters')
        params['facility_name']=facility_name.strip()
    if state_abbr: params['state_abbr']=_code(state_abbr,'state_abbr',2).upper()
    if city_name: params['city_name']=city_name.strip()[:80]
    if zip_code: params['zip_code']=_code(zip_code,'zip_code',10)
    if program_acronym: params['pgm_sys_acrnm']=_code(program_acronym,'program_acronym',24)
    if latitude is not None or longitude is not None or search_radius is not None:
        if latitude is None or longitude is None or search_radius is None: raise ValueError('latitude, longitude and search_radius must be supplied together')
        if not (-90<=float(latitude)<=90 and -180<=float(longitude)<=180 and 0<float(search_radius)<=25): raise ValueError('FRS coordinate/radius values are out of bounds')
        params.update({'latitude83':float(latitude),'longitude83':float(longitude),'search_radius':float(search_radius)})
    if len(params)==1 or (set(params)=={'output','state_abbr'}): raise ValueError('FRS public query requires a facility identifier/name, locality/program filter, ZIP, or bounded coordinate radius')
    base=_setting(settings,'epa_frs_base_url',_default_base('epa-frs-public-api'))
    endpoint=f"{base}?{urlencode(params)}"; data=shared._request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'epa-frs-public-api','mode':'LIVE','data':data,'provenance':{'organization':'U.S. Environmental Protection Agency','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[3]['boundary']}

def usgs_volcano_notices(settings, *, days:int=3, observatory:str=''):
    d=int(days)
    if not 1<=d<=7: raise ValueError('days must be between 1 and 7')
    obs=(observatory or '').strip().lower(); allowed={'','avo','calvo','cvo','hvo','nmi','yvo'}
    if obs not in allowed: raise ValueError('observatory is invalid')
    base=_setting(settings,'usgs_volcano_hans_base_url',_default_base('usgs-volcano-hans')).rstrip('/')
    endpoint=f'{base}/vonas/{d}' + (f'?{urlencode({"obs":obs})}' if obs else '')
    data=shared._request_json(endpoint,timeout=_timeout(settings))
    return {'ok':True,'version':VERSION,'connector_id':'usgs-volcano-hans','mode':'LIVE','days':d,'observatory':obs or None,'data':data,'provenance':{'organization':'U.S. Geological Survey Volcano Hazards Program','endpoint':endpoint,'retrieved_at':_now()},'boundary':NEW_CONNECTORS[4]['boundary']}
