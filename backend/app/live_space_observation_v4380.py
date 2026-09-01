from __future__ import annotations

"""Site Intelligence v4.39.1 — live Space observation and archive retrieval.

Provider lanes are independent and public by default. Release readiness never performs
upstream network probes and no provider failure fabricates observations, imagery,
ephemerides, exoplanets, or technosignature findings.
"""

from datetime import datetime, timedelta, timezone
import json, re
from typing import Any, Callable
from urllib.parse import quote, urlencode

from .version import APP_VERSION
from .external_resilience_v43517 import request_json as resilient_request_json, request_text as resilient_request_text, request_bytes as resilient_request_bytes

VERSION=APP_VERSION
CONTRACT='live-space-observation-planetary-imagery-archive-retrieval'
SCHEMA='sc-site-intelligence-live-space/1.0'
MAX_RESULTS=24
USGS_STAC='https://stac.astrogeology.usgs.gov/api'
MAST_INVOKE='https://mast.stsci.edu/api/v0/invoke'
HORIZONS='https://ssd-api.jpl.nasa.gov/horizons.api'
EXO_TAP='https://exoplanetarchive.ipac.caltech.edu/TAP/sync'
BREAKTHROUGH='https://breakthroughinitiatives.org/opendatasearch'

PROVIDERS=(
 {'id':'planetary-imagery','title':'Planetary imagery','organization':'USGS Astrogeology / NASA Solar System Treks','mode':'LIVE','evidence':['planetary STAC collection','planetary image/data asset'],'public_url':'https://stac.astrogeology.usgs.gov/','search_dimensions':['Moon/Mars','collection','asset']},
 {'id':'astronomy-observations','title':'Astronomical observations','organization':'MAST / STScI','mode':'LIVE','evidence':['telescope observation record','archive product context'],'public_url':'https://mast.stsci.edu/','search_dimensions':['RA/Dec','radius','target']},
 {'id':'solar-system-ephemeris','title':'Solar-system ephemeris','organization':'NASA JPL Solar System Dynamics','mode':'LIVE','evidence':['authoritative Horizons ephemeris response'],'public_url':'https://ssd.jpl.nasa.gov/horizons/','search_dimensions':['body','epoch','observer']},
 {'id':'exoplanets','title':'Exoplanets','organization':'NASA Exoplanet Archive / IPAC','mode':'LIVE','evidence':['planetary-system archive record'],'public_url':'https://exoplanetarchive.ipac.caltech.edu/','search_dimensions':['planet','host star']},
 {'id':'seti-archive','title':'SETI archive discovery','organization':'Breakthrough Listen','mode':'LIVE_DISCOVERY','evidence':['public archive metadata/handoff'],'public_url':BREAKTHROUGH,'search_dimensions':['target','archive metadata']},
)

BODY_IDS={'sun':'10','mercury':'199','venus':'299','earth':'399','moon':'301','mars':'499','jupiter':'599','saturn':'699','uranus':'799','neptune':'899','pluto':'999'}

def _now(): return datetime.now(timezone.utc).isoformat()
def _limit(v):
    try:return max(1,min(MAX_RESULTS,int(v or 12)))
    except (TypeError,ValueError):return 12
def _clean(v,n=300):return str(v or '').strip()[:n]
def _f(v,lo,hi,name):
    if v in (None,''):return None
    x=float(v)
    if not lo<=x<=hi:raise ValueError(f'{name} must be between {lo:g} and {hi:g}')
    return round(x,7)
def _timeout(settings):
    try:return max(2,min(20,int(getattr(settings,'space_observation_timeout_seconds',10))))
    except Exception:return 10

def provider_catalog(settings=None):
    return {'ok':True,'version':VERSION,'contract':CONTRACT,'schema':SCHEMA,'provider_count':len(PROVIDERS),'providers':[dict(p,configured=True,configuration_required=False) for p in PROVIDERS],'default_provider':'astronomy-observations','credential_required':False,'truth_boundaries':['Archive discovery is not a live telescope feed.','Planetary STAC assets retain product-specific processing and fitness-for-use limits.','Horizons output is authoritative ephemeris data for the submitted request; the local orientation diagram is not.','Exoplanet archive parameters retain their source/reference semantics and do not establish habitability.','SETI archive records and signal-search products are not confirmation of extraterrestrial intelligence.'],'generated_at':_now()}

def readiness(settings=None):
    checks={'five_live_lanes_registered':len(PROVIDERS)==5,'planetary_stac_public':True,'mast_public_query':True,'jpl_horizons_public':True,'nasa_exoplanet_tap_public':True,'breakthrough_archive_public':True,'credential_free_core_space':True,'bounded_results':MAX_RESULTS<=24,'network_free_readiness':True,'upstream_health_non_blocking':True}
    return {'ok':all(checks.values()),'version':VERSION,'contract':CONTRACT,'schema':SCHEMA,'checks':checks,'network_calls_performed':False,'release_blocking_upstream_health':False,'generated_at':_now()}

def _planetary(req,limit,request_json,timeout):
    body=_clean(req.get('body') or req.get('target') or 'moon',40).lower()
    if body not in {'moon','mars'}:raise ValueError('planetary imagery currently supports moon or mars')
    collections=request_json(f'{USGS_STAC}/collections',timeout=timeout,max_bytes=5_000_000,cache=True,stale_if_error=False)
    rows=collections.get('collections',[]) if isinstance(collections,dict) else []
    matches=[]
    needle='moon' if body=='moon' else 'mars'
    for row in rows:
        if not isinstance(row,dict):continue
        text=' '.join(map(str,[row.get('id',''),row.get('title',''),row.get('description','')])).lower()
        if needle in text or ('lunar' in text and body=='moon'):
            matches.append(row)
    results=[]
    for col in matches[:min(4,limit)]:
        cid=_clean(col.get('id'),200)
        if not cid:continue
        try:
            payload=request_json(f"{USGS_STAC}/search?{urlencode({'collections':cid,'limit':min(limit,8)})}",timeout=timeout,max_bytes=6_000_000,cache=True,stale_if_error=False)
            feats=payload.get('features',[]) if isinstance(payload,dict) else []
        except Exception:
            feats=[]
        if not feats:
            results.append({'provider':'planetary-imagery','record_type':'stac-collection','source_record_id':cid,'title':col.get('title') or cid,'body':body,'source_record_url':f'{USGS_STAC}/collections/{quote(cid)}','media_url':None,'preview_url':None,'metadata':{'description':_clean(col.get('description'),500)},'truth':'Collection discovery does not prove an image covers a selected coordinate.'})
        for feat in feats:
            if not isinstance(feat,dict):continue
            assets=feat.get('assets') if isinstance(feat.get('assets'),dict) else {}
            chosen=None
            for key,a in assets.items():
                if isinstance(a,dict) and str(a.get('href','')).startswith('http'):
                    roles=a.get('roles') or []
                    if any(r in {'thumbnail','overview','visual','data'} for r in roles) or key.lower() in {'thumbnail','browse','image','data'}:
                        chosen=a;break
            props=feat.get('properties') if isinstance(feat.get('properties'),dict) else {}
            fid=_clean(feat.get('id'),240)
            results.append({'provider':'planetary-imagery','record_type':'planetary-stac-item','source_record_id':fid,'title':props.get('title') or fid or cid,'body':body,'collection':feat.get('collection') or cid,'source_record_url':f'{USGS_STAC}/collections/{quote(cid)}/items/{quote(fid)}' if fid else f'{USGS_STAC}/collections/{quote(cid)}','media_url':chosen.get('href') if chosen else None,'preview_url':chosen.get('href') if chosen else None,'observed_at':props.get('datetime') or props.get('start_datetime'),'metadata':{'instrument':props.get('instrument') or props.get('instruments'),'platform':props.get('platform'),'asset_type':chosen.get('type') if chosen else None},'truth':'Asset is source-attributed planetary data; processing level and quantitative suitability remain product-specific.'})
            if len(results)>=limit:break
        if len(results)>=limit:break
    return results,{'body':body,'collections_matched':len(matches),'source_url':f'{USGS_STAC}/collections'}

def _mast(req,limit,request_bytes,timeout):
    ra=_f(req.get('ra_deg'),0,360,'ra_deg'); dec=_f(req.get('dec_deg'),-90,90,'dec_deg')
    presets={'m31':(10.6847083,41.26875),'orion':(83.82208,-5.39111),'proxima centauri':(217.42894,-62.67949),'trappist-1':(346.622,-5.041)}
    target=_clean(req.get('target'),120).lower()
    if ra is None or dec is None:
        ra,dec=presets.get(target,presets['m31'])
    radius=_f(req.get('radius_deg') or .1,.001,5,'radius_deg')
    request={'service':'Mast.Caom.Cone','params':{'ra':ra,'dec':dec,'radius':radius},'format':'json','pagesize':limit,'page':1}
    data=urlencode({'request':json.dumps(request,separators=(',',':'))}).encode()
    tr=request_bytes(MAST_INVOKE,method='POST',data=data,headers={'Content-Type':'application/x-www-form-urlencoded','Accept':'application/json'},timeout=timeout,max_bytes=6_000_000,cache=True,stale_if_error=False,retry_safe=True)
    payload=json.loads(tr.body.decode(tr.charset or 'utf-8'))
    rows=payload.get('data',[]) if isinstance(payload,dict) else []
    results=[]
    for row in rows[:limit]:
        if not isinstance(row,dict):continue
        obsid=_clean(row.get('obsid') or row.get('obs_id'),220)
        results.append({'provider':'astronomy-observations','record_type':'mast-observation','source_record_id':obsid,'title':row.get('target_name') or row.get('target_name_hlsp') or 'MAST observation','source_record_url':f'https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html?searchQuery={quote(str(row.get("target_name") or f"{ra},{dec}"))}','media_url':None,'preview_url':None,'ra_deg':row.get('s_ra'),'dec_deg':row.get('s_dec'),'observed_at':row.get('t_min'),'metadata':{'mission':row.get('obs_collection'),'instrument':row.get('instrument_name'),'filters':row.get('filters'),'data_rights':row.get('dataRights')},'truth':'Archive observation metadata is not a live telescope image; data products retain instrument/calibration context.'})
    return results,{'ra_deg':ra,'dec_deg':dec,'radius_deg':radius,'source_url':'https://mast.stsci.edu/'}

def _horizons(req,limit,request_json,timeout):
    body=_clean(req.get('body') or req.get('target') or 'mars',40).lower(); command=BODY_IDS.get(body,body)
    raw_epoch=_clean(req.get('epoch'),60)
    try:
        start=datetime.fromisoformat(raw_epoch.replace('Z','+00:00')) if raw_epoch else datetime.now(timezone.utc)
        if start.tzinfo is None:start=start.replace(tzinfo=timezone.utc)
        start=start.astimezone(timezone.utc)
    except ValueError as e:raise ValueError('epoch must be ISO-8601 compatible') from e
    stop=start+timedelta(days=1)
    params={'format':'json','COMMAND':f"'{command}'",'OBJ_DATA':'YES','MAKE_EPHEM':'YES','EPHEM_TYPE':'OBSERVER','CENTER':"'500@399'",'START_TIME':f"'{start.strftime('%Y-%m-%d %H:%M')}'",'STOP_TIME':f"'{stop.strftime('%Y-%m-%d %H:%M')}'",'STEP_SIZE':"'6 h'",'QUANTITIES':"'1,9,20,23,24'",'CSV_FORMAT':'YES'}
    url=f'{HORIZONS}?{urlencode(params)}'; payload=request_json(url,timeout=timeout,max_bytes=3_000_000,cache=True,stale_if_error=False)
    text=_clean(payload.get('result') if isinstance(payload,dict) else '',12000)
    if not text:raise RuntimeError('JPL Horizons returned no ephemeris text.')
    result={'provider':'solar-system-ephemeris','record_type':'jpl-horizons-ephemeris','source_record_id':f'{command}:{start.isoformat()}','title':f'{body.title()} ephemeris from JPL Horizons','source_record_url':url,'media_url':None,'preview_url':None,'observed_at':start.isoformat(),'metadata':{'body':body,'observer':'Earth geocenter','excerpt':text[:5000]},'truth':'Numerical values are JPL Horizons output for the submitted request; the local solar-system drawing is not an ephemeris.'}
    return [result],{'body':body,'epoch':start.isoformat(),'source_url':url}

def _exoplanets(req,limit,request_json,timeout):
    target=_clean(req.get('target'),120)
    columns='pl_name,hostname,discoverymethod,disc_year,pl_orbper,pl_rade,pl_bmasse,pl_eqt,sy_dist'
    query=f'select top {limit} {columns} from pscomppars'
    if target:
        safe=target.lower().replace("'","''");query+=f" where lower(pl_name) like '%{safe}%' or lower(hostname) like '%{safe}%'"
    query+=' order by pl_name'
    url=f'{EXO_TAP}?{urlencode({"query":query,"format":"json"})}'; payload=request_json(url,timeout=timeout,max_bytes=5_000_000,cache=True,stale_if_error=False)
    rows=payload if isinstance(payload,list) else []
    results=[]
    for row in rows[:limit]:
        if not isinstance(row,dict):continue
        name=_clean(row.get('pl_name'),160)
        results.append({'provider':'exoplanets','record_type':'exoplanet-archive-record','source_record_id':name,'title':name or 'Exoplanet record','source_record_url':'https://exoplanetarchive.ipac.caltech.edu/','media_url':None,'preview_url':None,'metadata':{'host':row.get('hostname'),'discovery_method':row.get('discoverymethod'),'discovery_year':row.get('disc_year'),'orbital_period_days':row.get('pl_orbper'),'radius_earth':row.get('pl_rade'),'mass_earth':row.get('pl_bmasse'),'equilibrium_temperature_k':row.get('pl_eqt'),'distance_pc':row.get('sy_dist')},'truth':'Archive parameters do not establish habitability, surface conditions, biosignatures, or life.'})
    return results,{'target':target or None,'source_url':url}

def _seti(req,limit,request_text,timeout):
    target=_clean(req.get('target'),120)
    html=request_text(BREAKTHROUGH,headers={'Accept':'text/html'},timeout=timeout,max_bytes=3_000_000,cache=True,stale_if_error=False)
    links=[]
    for href,label in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',html,re.I|re.S):
        plain=re.sub('<[^>]+>',' ',label);plain=re.sub(r'\s+',' ',plain).strip()
        hay=(plain+' '+href).lower()
        if target and target.lower() not in hay:continue
        if 'data' not in hay and 'archive' not in hay and 'search' not in hay:continue
        if href.startswith('/'):href='https://breakthroughinitiatives.org'+href
        if not href.startswith('http'):continue
        links.append({'provider':'seti-archive','record_type':'seti-archive-handoff','source_record_id':href,'title':plain[:180] or 'Breakthrough Listen archive record','source_record_url':href,'media_url':None,'preview_url':None,'metadata':{'target_filter':target or None},'truth':'Archive availability or signal-search output is not confirmation of a technosignature or extraterrestrial intelligence.'})
        if len(links)>=limit:break
    if not links:
        links=[{'provider':'seti-archive','record_type':'seti-archive-search','source_record_id':'breakthrough-listen-open-data','title':'Breakthrough Listen Open Data Archive','source_record_url':BREAKTHROUGH,'media_url':None,'preview_url':None,'metadata':{'target_filter':target or None,'machine_rows_parsed':0},'truth':'Use the public archive for source data. A candidate/event is not confirmation of extraterrestrial intelligence.'}]
    return links,{'target':target or None,'source_url':BREAKTHROUGH}

def search(request:dict[str,Any],settings=None,*,request_json=resilient_request_json,request_text=resilient_request_text,request_bytes=resilient_request_bytes):
    if not isinstance(request,dict):raise TypeError('request must be an object')
    provider=_clean(request.get('provider') or 'astronomy-observations',60)
    if provider not in {p['id'] for p in PROVIDERS}:raise ValueError(f'unsupported Space provider: {provider}')
    limit=_limit(request.get('limit'));timeout=_timeout(settings)
    try:
        if provider=='planetary-imagery':results,query=_planetary(request,limit,request_json,timeout)
        elif provider=='astronomy-observations':results,query=_mast(request,limit,request_bytes,timeout)
        elif provider=='solar-system-ephemeris':results,query=_horizons(request,limit,request_json,timeout)
        elif provider=='exoplanets':results,query=_exoplanets(request,limit,request_json,timeout)
        else:results,query=_seti(request,limit,request_text,timeout)
        state='ready' if results else 'empty'
        error=None
    except Exception as exc:
        results=[];query={'target':_clean(request.get('target'),120) or None};state='degraded';error=str(exc)[:500]
    return {'ok':state!='degraded','version':VERSION,'contract':CONTRACT,'schema':SCHEMA,'provider':provider,'state':state,'result_count':len(results),'results':results,'query':query,'error':error,'upstream_failure_release_blocking':False,'truth_boundaries':provider_catalog(settings)['truth_boundaries'],'retrieved_at':_now()}
