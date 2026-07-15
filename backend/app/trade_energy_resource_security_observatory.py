"""Trade, Energy, and Resource Security Observatory for Site Intelligence v2.6.0.

This public bridge combines free official economics, trade, energy, agriculture,
water, materials, and environmental records from Sustainable Catalyst Core.
It preserves provider units, periods, directions, counterpart geographies,
licenses, and reporting frequencies. It does not create a proprietary security
score, infer sanctions exposure, or fabricate missing records.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import math
import os
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .global_conditions_observatory import CoreReadConfig, _core_json, _items, _safe_text, _safe_url, core_read_config
from .live_country_intelligence import country_catalog

RELEASE_SCHEMA="sc-site-intelligence-trade-energy-resource-security/1.0"
RECORDS_SCHEMA="sc-site-intelligence-resource-security-records/1.0"
MAX_RECORDS=300
SENSITIVE_KEYS={"api_key","apikey","token","authorization","password","secret","credential","raw_record_id","write_api_key","public_api_key"}
FAMILY_LABELS={
 "trade":"Trade flows and market access",
 "energy":"Energy systems and electricity",
 "food-agriculture":"Food and agriculture",
 "water":"Water resources and stress",
 "materials":"Materials and strategic resources",
 "supply-chain":"Supply-chain exposure",
 "climate-transition":"Climate and transition context",
 "other":"Other official resource record",
}

@dataclass(frozen=True)
class ObservatoryConfig:
    enabled: bool
    timeout_seconds: float
    cache_ttl_seconds: int

def _as_bool(value:Any,default:bool=False)->bool:
    if isinstance(value,bool): return value
    if value is None: return default
    return str(value).strip().lower() in {"1","true","yes","on","enabled"}

def observatory_config(settings:Any=None)->ObservatoryConfig:
    enabled=getattr(settings,"trade_energy_resource_security_enabled",None)
    if enabled is None: enabled=os.getenv("SC_SI_TRADE_ENERGY_RESOURCE_SECURITY_ENABLED","true")
    timeout=getattr(settings,"trade_energy_resource_security_timeout_seconds",None)
    if timeout is None: timeout=os.getenv("SC_SI_TRADE_ENERGY_RESOURCE_SECURITY_TIMEOUT_SECONDS","9")
    ttl=getattr(settings,"trade_energy_resource_security_cache_ttl_seconds",None)
    if ttl is None: ttl=os.getenv("SC_SI_TRADE_ENERGY_RESOURCE_SECURITY_CACHE_TTL_SECONDS","120")
    return ObservatoryConfig(_as_bool(enabled,True),max(2.0,min(float(timeout),30.0)),max(15,min(int(ttl),1800)))

def _core_config(settings:Any=None)->CoreReadConfig:
    base=core_read_config(settings); local=observatory_config(settings)
    return CoreReadConfig(bool(base.enabled and local.enabled),base.base_url,base.api_key,local.timeout_seconds,local.cache_ttl_seconds)

def _sensitive_key(value:Any)->bool:
    token=''.join(ch for ch in str(value or '').lower() if ch.isalnum())
    return token in {"key","rawrecordid"} or any(x in token for x in ("apikey","token","authorization","password","secret","credential"))

def _public_url(value:Any)->str:
    safe=_safe_url(value)
    if not safe:return ""
    parts=urlsplit(safe)
    query=[(k,v) for k,v in parse_qsl(parts.query,keep_blank_values=True) if not _sensitive_key(k)]
    return urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode(query,doseq=True),parts.fragment))

def _safe_mapping(value:Any,depth:int=0)->dict[str,Any]:
    if not isinstance(value,Mapping) or depth>2:return {}
    out={}
    for k,v in value.items():
        key=_safe_text(k,80)
        if not key or key.lower() in SENSITIVE_KEYS or _sensitive_key(key):continue
        if isinstance(v,Mapping):
            child=_safe_mapping(v,depth+1)
            if child:out[key]=child
        elif isinstance(v,list):out[key]=[_safe_text(x,240) if not isinstance(x,(bool,int,float)) else x for x in v[:30] if not isinstance(x,(dict,list))]
        elif v is None or isinstance(v,(bool,int,float)):out[key]=v
        else:out[key]=_safe_text(v,500)
    return out

def _number(value:Any)->float|None:
    try:n=float(value)
    except (TypeError,ValueError):return None
    return n if math.isfinite(n) else None

def _family(record:Mapping[str,Any])->str:
    text=' '.join(str(record.get(k) or '').lower() for k in ("record_type","subject","indicator_code","indicator_name","dataset_id","unit","notes","metric","domain"))
    if any(x in text for x in ("trade","import","export","tariff","commodity flow","comtrade","balance of trade")):return "trade"
    if any(x in text for x in ("energy","electric","power generation","renewable","fuel","petroleum","gas","coal","solar","wind","hydro","eia")):return "energy"
    if any(x in text for x in ("agricultur","crop","food","livestock","fao","fertilizer","yield","cereal","fishery")):return "food-agriculture"
    if any(x in text for x in ("water","aquastat","withdrawal","freshwater","irrigation","water stress","groundwater","streamflow")):return "water"
    if any(x in text for x in ("material","mineral","metal","lithium","cobalt","copper","rare earth","cement","steel")):return "materials"
    if any(x in text for x in ("supply chain","input-output","dependency","concentration","counterpart","partner")):return "supply-chain"
    if any(x in text for x in ("emission","carbon","climate","transition","greenhouse","decarbon","sdg 7","sdg7")):return "climate-transition"
    return "other"

def _status(record:Mapping[str,Any])->str:
    raw=_safe_text(record.get("status"),80).lower().replace('-','_').replace(' ','_')
    labels={"official_release":"OFFICIAL RELEASE","latest_available":"LATEST AVAILABLE","delayed":"DELAYED","end_of_day":"END OF DAY","stale":"STALE"}
    if raw in labels:return labels[raw]
    freq=_safe_text(record.get("frequency"),40).upper()
    return freq or "LATEST AVAILABLE"

def _public_record(record:Mapping[str,Any])->dict[str,Any]:
    dimensions=_safe_mapping(record.get("dimensions"))
    out={
      "id":_safe_text(record.get("id") or record.get("record_id"),180),
      "source_id":_safe_text(record.get("source_id"),160),
      "connector_id":_safe_text(record.get("connector_id"),180),
      "record_type":_safe_text(record.get("record_type") or "official_statistic",100),
      "subject":_safe_text(record.get("subject"),180),
      "indicator_code":_safe_text(record.get("indicator_code"),180),
      "indicator_name":_safe_text(record.get("indicator_name") or record.get("metric") or record.get("title"),420),
      "dataset_id":_safe_text(record.get("dataset_id"),180),
      "geography_code":_safe_text(record.get("geography_code") or record.get("country_code"),20).upper(),
      "geography_name":_safe_text(record.get("geography_name"),180),
      "counterpart_code":_safe_text(record.get("counterpart_code") or dimensions.get("counterpart_code") or dimensions.get("partner"),20).upper(),
      "period":_safe_text(record.get("period") or record.get("observed_at"),80),
      "frequency":_safe_text(record.get("frequency"),40),
      "value_number":_number(record.get("value_number") if record.get("value_number") is not None else record.get("value")),
      "value_text":_safe_text(record.get("value_text"),500),
      "unit":_safe_text(record.get("unit"),160),
      "status":_status(record),
      "notes":_safe_text(record.get("notes") or record.get("description"),1200),
      "source_url":_public_url(record.get("source_url") or record.get("canonical_url")),
      "license_name":_safe_text(record.get("license_name") or record.get("license"),180),
      "attribution":_safe_text(record.get("attribution"),400),
      "dimensions":dimensions,
    }
    out["family"]=_family(out);out["family_label"]=FAMILY_LABELS[out["family"]]
    return out

def _fetch(settings:Any,params:Mapping[str,Any])->tuple[list[dict[str,Any]],dict[str,Any]]:
    local=observatory_config(settings);core=_core_config(settings)
    if not local.enabled:raise RuntimeError("The trade, energy, and resource-security workspace is disabled.")
    if not core.configured:raise RuntimeError("Platform Core public data reading is not configured.")
    query={k:v for k,v in dict(params).items() if v not in (None,"")}
    query["limit"]=min(max(int(query.get("limit") or 100),1),MAX_RECORDS)
    payload=_core_json(core,"/api/v1/economics/records",query,cache_key="resource-security:"+'&'.join(f"{k}={query[k]}" for k in sorted(query)))
    records=[_public_record(x) for x in _items(payload,"items","records")]
    meta=payload.get("meta") if isinstance(payload,dict) and isinstance(payload.get("meta"),dict) else {}
    return records,meta

def _integration(settings:Any,error:str="")->dict[str,Any]:
    local=observatory_config(settings);core=core_read_config(settings)
    if not local.enabled:state,msg="disabled","The resource-security workspace is disabled by configuration."
    elif not core.configured:state,msg="core-unconfigured","Platform Core is not configured; no trade, energy, or resource records are fabricated locally."
    elif error:state,msg="degraded",error
    else:state,msg="connected","Official trade, energy, agriculture, water, and resource records are available through the public Core bridge."
    return {"enabled":local.enabled,"configured":bool(local.enabled and core.configured),"state":state,"message":msg,"credential_exposed":False}

def build_records(settings:Any=None,*,family:str="",source_id:str="",geography_code:str="",counterpart_code:str="",indicator_code:str="",frequency:str="",query:str="",start:str="",end:str="",limit:int=150,offset:int=0)->dict[str,Any]:
    params={"source_id":source_id,"geography_code":geography_code.upper(),"counterpart_code":counterpart_code.upper(),"indicator_code":indicator_code,"frequency":frequency,"query":query,"start":start,"end":end,"limit":min(max(int(limit),1),MAX_RECORDS),"offset":max(int(offset),0)}
    try:records,meta=_fetch(settings,params);integration=_integration(settings)
    except RuntimeError as exc:records,meta=[],{};integration=_integration(settings,str(exc))
    if family:records=[r for r in records if r["family"]==family]
    return {"ok":True,"schema":RECORDS_SCHEMA,"version":"2.6.0","generated_at":datetime.now(timezone.utc).isoformat(),"integration":integration,"filters":{**params,"family":family},"total":len(records),"records":records,"meta":meta}

def build_facets(settings:Any=None,*,geography_code:str="")->dict[str,Any]:
    payload=build_records(settings,geography_code=geography_code,limit=MAX_RECORDS)
    recs=payload["records"]
    def counts(key):return [{"id":k,"count":v} for k,v in sorted(Counter(r.get(key) for r in recs if r.get(key)).items())]
    return {"ok":True,"schema":RELEASE_SCHEMA,"version":"2.6.0","integration":payload["integration"],"families":[{"id":k,"label":v,"count":sum(1 for r in recs if r["family"]==k)} for k,v in FAMILY_LABELS.items()],"sources":counts("source_id"),"geographies":counts("geography_code"),"counterparts":counts("counterpart_code"),"indicators":counts("indicator_code"),"frequencies":counts("frequency")}

def _family_view(settings:Any,family:str,**kwargs)->dict[str,Any]:
    data=build_records(settings,family=family,limit=kwargs.pop("limit",MAX_RECORDS),**kwargs)
    return {"ok":True,"schema":RELEASE_SCHEMA,"version":"2.6.0","family":family,"family_label":FAMILY_LABELS[family],"integration":data["integration"],"total":len(data["records"]),"records":data["records"],"warning":"Values with different units, periods, directions, or definitions must not be added or ranked without review."}

def build_trade(settings:Any=None,**kwargs):return _family_view(settings,"trade",**kwargs)
def build_energy(settings:Any=None,**kwargs):return _family_view(settings,"energy",**kwargs)
def build_resources(settings:Any=None,**kwargs):
    payload=build_records(settings,limit=kwargs.pop("limit",MAX_RECORDS),**kwargs)
    keep={"food-agriculture","water","materials","supply-chain","climate-transition"};records=[r for r in payload["records"] if r["family"] in keep]
    return {"ok":True,"schema":RELEASE_SCHEMA,"version":"2.6.0","integration":payload["integration"],"total":len(records),"records":records,"warning":"Resource records retain provider units and do not establish scarcity, strategic importance, or national security risk by themselves."}

def build_dependencies(settings:Any=None,*,geography_code:str="",family:str="trade",limit:int=250)->dict[str,Any]:
    payload=build_records(settings,family=family,geography_code=geography_code,limit=limit)
    exposures=[]
    for r in payload["records"]:
        if not r.get("counterpart_code"):continue
        exposures.append({"geography_code":r.get("geography_code"),"counterpart_code":r.get("counterpart_code"),"indicator_code":r.get("indicator_code"),"indicator_name":r.get("indicator_name"),"period":r.get("period"),"value_number":r.get("value_number"),"unit":r.get("unit"),"source_id":r.get("source_id"),"source_url":r.get("source_url")})
    return {"ok":True,"schema":RELEASE_SCHEMA,"version":"2.6.0","integration":payload["integration"],"geography_code":geography_code.upper(),"family":family,"count":len(exposures),"exposures":exposures,"methodology":{"risk_score_created":False,"share_calculated":False,"statement":"This view lists published counterpart relationships. It does not infer dependency, vulnerability, coercion, sanctions exposure, or supply disruption probability."}}

def build_country_profile(settings:Any=None,*,country:str,limit:int=MAX_RECORDS)->dict[str,Any]:
    code=_safe_text(country,20).upper()
    if len(code)<2:raise ValueError("A country or geography code is required.")
    payload=build_records(settings,geography_code=code,limit=limit)
    fam=Counter(r["family"] for r in payload["records"]);sources=Counter(r["source_id"] for r in payload["records"] if r.get("source_id"));units=Counter(r["unit"] for r in payload["records"] if r.get("unit"))
    catalog=country_catalog();country_meta=next((c for c in catalog.get("countries",[]) if c.get("code")==code),{"code":code,"name":code})
    return {"ok":True,"schema":RELEASE_SCHEMA,"version":"2.6.0","integration":payload["integration"],"country":country_meta,"counts":{"records":len(payload["records"]),"sources":len(sources),"indicators":len({r.get('indicator_code') or r.get('indicator_name') for r in payload['records']}),"counterparts":len({r.get('counterpart_code') for r in payload['records'] if r.get('counterpart_code')})},"families":[{"id":k,"label":FAMILY_LABELS[k],"count":fam.get(k,0)} for k in FAMILY_LABELS],"sources":[{"id":k,"count":v} for k,v in sources.most_common()],"units":[{"id":k,"count":v} for k,v in units.most_common()],"records":payload["records"],"boundary":"Coverage is not a resource-security score and does not establish resilience, vulnerability, or strategic risk."}

def build_overview(settings:Any=None)->dict[str,Any]:
    data=build_records(settings,limit=MAX_RECORDS);recs=data["records"];fam=Counter(r["family"] for r in recs)
    return {"ok":True,"schema":RELEASE_SCHEMA,"version":"2.6.0","release_name":"Trade, Energy, and Resource Security Observatory","generated_at":datetime.now(timezone.utc).isoformat(),"integration":data["integration"],"counts":{"records":len(recs),"sources":len({r['source_id'] for r in recs if r.get('source_id')}),"geographies":len({r['geography_code'] for r in recs if r.get('geography_code')}),"counterparts":len({r['counterpart_code'] for r in recs if r.get('counterpart_code')})},"families":[{"id":k,"label":v,"count":fam.get(k,0)} for k,v in FAMILY_LABELS.items()],"source_policy":{"paid_api_required":False,"licensed_realtime_market_data":False,"fabricated_records":False},"interpretation":{"security_score":False,"causal_inference":False,"forecasting":False,"statement":"The observatory organizes official evidence. It does not assign national-security risk, predict shortages, recommend trades, or determine policy."}}

def build_brief(settings:Any=None,*,geography_code:str="",family:str="",query:str="",limit:int=100)->dict[str,Any]:
    data=build_records(settings,geography_code=geography_code,family=family,query=query,limit=limit);recs=data["records"]
    return {"ok":True,"schema":"sc-site-intelligence-resource-security-brief/1.0","version":"2.6.0","generated_at":datetime.now(timezone.utc).isoformat(),"title":f"Trade, energy, and resource evidence{(' — '+geography_code.upper()) if geography_code else ''}","integration":data["integration"],"filters":{"geography_code":geography_code.upper(),"family":family,"query":query},"summary":{"records":len(recs),"sources":len({r['source_id'] for r in recs if r.get('source_id')}),"families":Counter(r['family'] for r in recs)},"records":recs[:80],"limitations":["Published values can use incompatible units, price bases, classifications, periods, and geographic definitions.","Counterpart relationships do not by themselves establish dependency or vulnerability.","This is public research support, not investment, trade, engineering, legal, sanctions, or national-security advice."]}

def build_diagnostics(settings:Any=None)->dict[str,Any]:
    local=observatory_config(settings);core=_core_config(settings)
    return {"ok":True,"schema":RELEASE_SCHEMA,"version":"2.6.0","integration":_integration(settings),"configuration":{"enabled":local.enabled,"core_configured":core.configured,"timeout_seconds":local.timeout_seconds,"cache_ttl_seconds":local.cache_ttl_seconds,"credential_exposed":False},"public_safety":{"paid_api_required":False,"proprietary_risk_score":False,"sanctions_screening":False,"investment_advice":False,"national_security_determination":False,"fabricated_records":False},"routes":["/public/trade-energy-resources","/public/trade-energy-resources/records","/public/trade-energy-resources/facets","/public/trade-energy-resources/trade","/public/trade-energy-resources/energy","/public/trade-energy-resources/resources","/public/trade-energy-resources/dependencies","/public/trade-energy-resources/country-profile","/public/trade-energy-resources/brief"]}
