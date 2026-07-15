"""Humanitarian, Conflict, and Displacement Observatory for Site Intelligence v2.5.0.

The observatory combines the existing source-aware event layer with public
records available through Sustainable Catalyst Core. It does not infer legal
responsibility, combatant status, refugee status, eligibility, casualty totals,
or severity rankings. It never substitutes demonstration records when sources
are unavailable.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .global_conditions_observatory import CoreReadConfig, _core_json, _items, _safe_text, _safe_url, core_read_config
from .unified_live_events import unified_events

RELEASE_SCHEMA = "sc-site-intelligence-humanitarian-conflict-displacement/1.0"
RECORDS_SCHEMA = "sc-site-intelligence-humanitarian-records/1.0"
TIMELINE_SCHEMA = "sc-site-intelligence-humanitarian-timeline/1.0"
MAX_RECORDS = 300
MAX_EVENTS = 500

CATEGORY_LABELS = {
    "humanitarian": "Humanitarian response",
    "displacement": "Displacement and mobility",
    "conflict": "Conflict and civilian protection",
    "food-water-health": "Food, water, shelter, and health",
    "rights-protection": "Rights and protection",
    "governance-response": "Governance and institutional response",
    "hazard-exposure": "Hazard exposure",
    "other": "Other public record",
}
STATE_ORDER = {"critical": 0, "high": 1, "moderate": 2, "low": 3, "unknown": 4}
SENSITIVE_KEYS = {"api_key", "apikey", "token", "authorization", "password", "secret", "credential", "raw_record_id", "write_api_key", "public_api_key"}

@dataclass(frozen=True)
class ObservatoryConfig:
    enabled: bool
    timeout_seconds: float
    cache_ttl_seconds: int


def _as_bool(value: Any, default: bool=False) -> bool:
    if isinstance(value, bool): return value
    if value is None: return default
    return str(value).strip().lower() in {"1","true","yes","on","enabled"}


def observatory_config(settings: Any=None) -> ObservatoryConfig:
    enabled=getattr(settings,"humanitarian_conflict_displacement_enabled",None)
    if enabled is None: enabled=os.getenv("SC_SI_HUMANITARIAN_CONFLICT_DISPLACEMENT_ENABLED","true")
    timeout=getattr(settings,"humanitarian_conflict_displacement_timeout_seconds",None)
    if timeout is None: timeout=os.getenv("SC_SI_HUMANITARIAN_CONFLICT_DISPLACEMENT_TIMEOUT_SECONDS","9")
    ttl=getattr(settings,"humanitarian_conflict_displacement_cache_ttl_seconds",None)
    if ttl is None: ttl=os.getenv("SC_SI_HUMANITARIAN_CONFLICT_DISPLACEMENT_CACHE_TTL_SECONDS","90")
    return ObservatoryConfig(_as_bool(enabled,True),max(2.0,min(float(timeout),30.0)),max(15,min(int(ttl),1800)))


def _core_config(settings: Any=None) -> CoreReadConfig:
    base=core_read_config(settings); local=observatory_config(settings)
    return CoreReadConfig(bool(base.enabled and local.enabled),base.base_url,base.api_key,local.timeout_seconds,local.cache_ttl_seconds)


def _sensitive_key(value: Any) -> bool:
    token=''.join(ch for ch in str(value or '').lower() if ch.isalnum())
    return token in {"key","rawrecordid"} or any(x in token for x in ("apikey","token","authorization","password","secret","credential"))


def _public_url(value: Any) -> str:
    safe=_safe_url(value)
    if not safe: return ""
    parts=urlsplit(safe)
    query=[(k,v) for k,v in parse_qsl(parts.query,keep_blank_values=True) if not _sensitive_key(k)]
    return urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode(query,doseq=True),parts.fragment))


def _safe_list(value: Any, limit: int=40) -> list[str]:
    if not isinstance(value,list): return []
    out=[]
    for item in value[:limit]:
        clean=_safe_text(item,240)
        if clean and clean not in out: out.append(clean)
    return out


def _safe_mapping(value: Any, depth: int=0) -> dict[str,Any]:
    if not isinstance(value,Mapping) or depth>2: return {}
    out={}
    for k,v in value.items():
        key=_safe_text(k,80)
        if not key or key.lower() in SENSITIVE_KEYS or _sensitive_key(key): continue
        if isinstance(v,Mapping):
            nested=_safe_mapping(v,depth+1)
            if nested: out[key]=nested
        elif isinstance(v,list): out[key]=[_safe_text(x,240) if not isinstance(x,(bool,int,float)) else x for x in v[:30] if x is not None and not isinstance(x,(dict,list))]
        elif v is None or isinstance(v,(bool,int,float)): out[key]=v
        else: out[key]=_safe_text(v,500)
    return out


def _category(record: Mapping[str,Any]) -> str:
    text=' '.join(str(record.get(k) or '').lower() for k in ("title","summary","description","record_type","domain","metric","subjects","indicator_name","category"))
    if any(x in text for x in ("human rights","protection","child protection","gender-based","rights recommendation","human_rights_recommendation","ohchr")): return "rights-protection"
    if any(x in text for x in ("refugee","displacement","displaced","asylum","migration","returnee","mobility")): return "displacement"
    if any(x in text for x in ("conflict","violence","civilian","attack","hostilit","armed")): return "conflict"
    if any(x in text for x in ("food","nutrition","water","sanitation","health","shelter","disease","famine")): return "food-water-health"
    if any(x in text for x in ("resolution","treaty","security council","general assembly","governance","institutional response")): return "governance-response"
    if any(x in text for x in ("earthquake","flood","storm","wildfire","drought","cyclone","volcano","hazard")): return "hazard-exposure"
    if any(x in text for x in ("humanitarian","relief","emergency","appeal","needs assessment","ocha","unhcr")): return "humanitarian"
    return "other"


def _severity(record: Mapping[str,Any]) -> str:
    value=_safe_text(record.get("severity") or record.get("risk_level") or record.get("priority"),50).lower()
    if value in STATE_ORDER: return value
    text=' '.join(str(record.get(k) or '').lower() for k in ("title","summary","description","status"))
    if any(x in text for x in ("catastrophic","critical","famine","emergency level")): return "critical"
    if any(x in text for x in ("severe","high risk","major emergency")): return "high"
    return "unknown"


def _date(record: Mapping[str,Any]) -> str:
    return _safe_text(record.get("observed_at") or record.get("published_at") or record.get("publication_date") or record.get("period") or record.get("created_at"),60)


def _countries(record: Mapping[str,Any]) -> list[str]:
    values=[]
    for key in ("countries","country_codes","geographies"):
        values.extend(_safe_list(record.get(key),20))
    single=_safe_text(record.get("country_code") or record.get("geography_code") or record.get("country"),80)
    if single: values.append(single)
    return list(dict.fromkeys(values))[:20]


def _public_record(record: Mapping[str,Any], source_kind: str="core") -> dict[str,Any]:
    title=_safe_text(record.get("title") or record.get("indicator_name") or record.get("metric") or record.get("name"),500) or "Untitled public record"
    source_id=_safe_text(record.get("source_id") or record.get("source") or record.get("provider"),160)
    output={
        "id": _safe_text(record.get("id") or record.get("record_id") or record.get("source_record_id"),200),
        "source_kind": source_kind,
        "source_id": source_id,
        "connector_id": _safe_text(record.get("connector_id"),180),
        "record_type": _safe_text(record.get("record_type") or record.get("domain") or "public_record",120),
        "category": _category(record),
        "title": title,
        "summary": _safe_text(record.get("summary") or record.get("description") or record.get("notes"),1400),
        "date": _date(record),
        "countries": _countries(record),
        "subjects": _safe_list(record.get("subjects") or record.get("keywords"),30),
        "severity": _severity(record),
        "status": _safe_text(record.get("status") or record.get("legal_status") or record.get("quality_status") or record.get("data_state"),100),
        "value": record.get("value") if isinstance(record.get("value"),(int,float)) else None,
        "unit": _safe_text(record.get("unit"),100),
        "frequency": _safe_text(record.get("frequency"),80),
        "source_url": _public_url(record.get("source_url") or record.get("canonical_source_url") or record.get("canonical_url") or record.get("landing_page_url")),
        "attribution": _safe_text(record.get("attribution") or record.get("source_name"),300),
        "license": _safe_text(record.get("license_name") or record.get("license"),200),
        "confidence": record.get("confidence") if isinstance(record.get("confidence"),(int,float)) else None,
        "metadata": _safe_mapping(record.get("metadata")),
    }
    if not output["id"]:
        output["id"]='hcd:'+str(abs(hash((output["source_id"],title,output["date"]))))
    return output


def _event_record(record: Mapping[str,Any]) -> dict[str,Any]:
    base=dict(record)
    base["subjects"]=[record.get("category_label") or record.get("category")]
    base["source_url"]=record.get("source_url")
    base["countries"]=[record.get("country_code")] if record.get("country_code") else []
    item=_public_record(base,"site-intelligence-event")
    coords=record.get("coordinates")
    if isinstance(coords,list) and len(coords)>=2:
        item["geometry"]={"type":"Point","coordinates":[coords[0],coords[1]]}
    return item


def _core_payloads(config: CoreReadConfig, *, country: str="", query: str="", limit: int=150) -> tuple[list[dict[str,Any]],dict[str,str]]:
    paths=[
        ("live","/api/v1/live/observations/latest",{"limit":limit}),
        ("law","/api/v1/international-law/records",{"limit":limit,"country":country,"query":query}),
        ("economics","/api/v1/economics/records",{"limit":limit,"geography_code":country,"query":query}),
    ]
    records=[]; states={}
    for kind,path,params in paths:
        try:
            payload=_core_json(config,path,params,cache_key=f"hcd:{kind}:{country}:{query}:{limit}")
            rows=_items(payload,"records","observations","items")
            for row in rows:
                item=_public_record(row,kind)
                if item["category"]!="other" or query:
                    records.append(item)
            states[kind]="connected"
        except RuntimeError:
            states[kind]="unavailable"
    return records,states


def _matches(item: Mapping[str,Any], *, country: str="", category: str="", source_id: str="", query: str="") -> bool:
    if country and country.upper() not in {str(x).upper() for x in item.get("countries",[])}: return False
    if category and item.get("category")!=category: return False
    if source_id and item.get("source_id")!=source_id: return False
    if query:
        hay=' '.join(str(item.get(k) or '') for k in ("title","summary","record_type","source_id","subjects","countries")).lower()
        if query.lower() not in hay: return False
    return True


def build_records(settings: Any=None, *, country: str="", category: str="", source_id: str="", query: str="", days: int=30, include_hazards: bool=True, limit: int=150, offset: int=0) -> dict[str,Any]:
    local=observatory_config(settings); core=_core_config(settings)
    generated=datetime.now(timezone.utc).isoformat()
    if not local.enabled:
        return {"ok":True,"schema":RECORDS_SCHEMA,"version":"2.5.0","generated_at":generated,"state":"disabled","records":[],"count":0,"source_states":{}}
    records=[]; source_states={}
    core_records=[]
    if core.configured:
        core_records,source_states=_core_payloads(core,country=country,query=query,limit=min(MAX_RECORDS,limit+offset+50))
        records.extend(core_records)
    else:
        source_states={"core":"unconfigured"}
    event_categories=["humanitarian","displacement","conflict"]
    if include_hazards: event_categories += ["earthquake","wildfire","storm","flood","volcano","extreme-heat","drought"]
    events=unified_events(days=max(1,min(days,90)),limit=min(MAX_EVENTS,limit+offset+100),categories=event_categories,country_code=country or None,allow_fallback=False)
    records.extend(_event_record(row) for row in events.get("events",[]))
    source_states.update({f"events:{k}":v for k,v in (events.get("source_states") or {}).items()})
    clean=[item for item in records if _matches(item,country=country,category=category,source_id=source_id,query=query)]
    dedup={}
    for item in clean:
        key=(item.get("source_id"),item.get("id"),item.get("title"),item.get("date")); dedup[key]=item
    ordered=sorted(dedup.values(),key=lambda x:(STATE_ORDER.get(x.get("severity"),4),x.get("date") or ""))
    page=ordered[offset:offset+max(1,min(limit,MAX_RECORDS))]
    state="connected" if page and any(v=="connected" for v in source_states.values()) else (events.get("data_state") or ("core-unconfigured" if not core.configured else "unavailable"))
    return {"ok":True,"schema":RECORDS_SCHEMA,"version":"2.5.0","generated_at":generated,"state":state,"records":page,"count":len(page),"total":len(ordered),"source_states":source_states,"fallback_used":False,"credential_exposed":False}


def build_overview(settings: Any=None) -> dict[str,Any]:
    payload=build_records(settings,limit=120)
    counts=Counter(item["category"] for item in payload["records"])
    countries=Counter(c for item in payload["records"] for c in item.get("countries",[]))
    return {"ok":True,"schema":RELEASE_SCHEMA,"version":"2.5.0","release_name":"Humanitarian, Conflict, and Displacement Observatory","generated_at":payload["generated_at"],"state":payload["state"],"counts":{"records":payload["total"],"categories":len(counts),"countries":len(countries),"sources":len({x.get('source_id') for x in payload['records'] if x.get('source_id')})},"category_counts":dict(counts),"top_countries":[{"country":k,"count":v} for k,v in countries.most_common(12)],"source_states":payload["source_states"],"governance":{"fabricated_records":False,"legal_responsibility_inference":False,"individual_risk_scoring":False,"refugee_status_determination":False,"military_targeting":False,"emergency_warning":False},"paid_provider_required":False}


def build_facets(settings: Any=None) -> dict[str,Any]:
    payload=build_records(settings,limit=MAX_RECORDS)
    rows=payload["records"]
    def vals(key): return sorted({str(v) for row in rows for v in (row.get(key) if isinstance(row.get(key),list) else [row.get(key)]) if v})
    return {"ok":True,"version":"2.5.0","state":payload["state"],"categories":[{"id":k,"label":v,"count":sum(1 for r in rows if r['category']==k)} for k,v in CATEGORY_LABELS.items()],"countries":vals("countries"),"sources":vals("source_id"),"record_types":vals("record_type")}


def build_timeline(settings: Any=None, **filters: Any) -> dict[str,Any]:
    payload=build_records(settings,limit=MAX_RECORDS,**filters)
    events=sorted(({"record_id":r["id"],"date":r["date"],"title":r["title"],"category":r["category"],"severity":r["severity"],"source_id":r["source_id"],"countries":r["countries"]} for r in payload["records"] if r.get("date")),key=lambda x:x["date"])
    return {"ok":True,"schema":TIMELINE_SCHEMA,"version":"2.5.0","state":payload["state"],"events":events,"count":len(events)}


def build_displacement(settings: Any=None, *, country: str="", limit: int=200) -> dict[str,Any]:
    payload=build_records(settings,country=country,category="displacement",include_hazards=False,limit=limit)
    numeric=[r for r in payload["records"] if isinstance(r.get("value"),(int,float))]
    return {"ok":True,"version":"2.5.0","state":payload["state"],"country":country,"records":payload["records"],"counts":{"records":len(payload["records"]),"numeric_observations":len(numeric)},"warning":"Stocks, flows, registrations, estimates, and assessment figures remain separate and must not be added without methodological review."}


def build_country_profile(settings: Any=None, *, country: str="", limit: int=250) -> dict[str,Any]:
    if not country: raise ValueError("country is required.")
    payload=build_records(settings,country=country,limit=limit)
    counts=Counter(r["category"] for r in payload["records"])
    return {"ok":True,"version":"2.5.0","state":payload["state"],"country":country.upper(),"counts":{"records":len(payload["records"]),"sources":len({r['source_id'] for r in payload['records'] if r['source_id']})},"category_counts":dict(counts),"records":payload["records"],"interpretation":"Record presence describes available public evidence, not complete incidence, severity, legal responsibility, need, or eligibility."}


def build_access_snapshot(settings: Any=None, *, country: str="", limit: int=200) -> dict[str,Any]:
    payload=build_records(settings,country=country,limit=limit)
    access=[r for r in payload["records"] if r["category"] in {"food-water-health","humanitarian","rights-protection"}]
    return {"ok":True,"version":"2.5.0","state":payload["state"],"country":country,"records":access,"count":len(access),"dimensions":["food","water","health","shelter","protection","humanitarian access"],"warning":"This is public research context, not an operational access assessment or emergency instruction."}


def build_brief(settings: Any=None, *, country: str="", category: str="", query: str="", limit: int=100) -> dict[str,Any]:
    payload=build_records(settings,country=country,category=category,query=query,limit=limit)
    counts=Counter(r["category"] for r in payload["records"])
    return {"ok":True,"version":"2.5.0","title":"Humanitarian, conflict, and displacement source brief","state":payload["state"],"filters":{"country":country,"category":category,"query":query},"summary":{"records":len(payload["records"]),"categories":dict(counts)},"records":payload["records"],"limitations":["Public records are incomplete and source-dependent.","Casualty, displacement, and affected-population figures may be revised.","The brief does not determine legal responsibility, civilian status, protection status, eligibility, or operational priority."]}


def build_diagnostics(settings: Any=None) -> dict[str,Any]:
    local=observatory_config(settings); core=_core_config(settings)
    return {"ok":True,"version":"2.5.0","enabled":local.enabled,"core_configured":core.configured,"credential_exposed":False,"fallback_records":False,"public_safety":{"legal_advice":False,"emergency_warning":False,"individual_risk_scoring":False,"military_targeting":False,"refugee_status_determination":False},"sources":["Site Intelligence unified public events","Sustainable Catalyst Core public live observations","Sustainable Catalyst Core international-law records","Sustainable Catalyst Core official statistics"]}
