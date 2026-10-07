from __future__ import annotations
from copy import deepcopy
import hashlib, json
from pathlib import Path
from typing import Any, Mapping
from .spatial_research_handoffs_v4510 import validate_research_object
from .version import APP_VERSION
REGISTRY_SCHEMA="sc-site-intelligence-advanced-domain-workspace-registry/1.0"
REGISTRY_PATH=Path(__file__).resolve().parents[1]/"data"/"advanced_domain_workspace_registry_v4530.json"

def _canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str).encode()
def _digest(v): return "sha256:"+hashlib.sha256(_canon(v)).hexdigest()
def _text(v,n=800): return " ".join(str(v or "").strip().split())[:n]
def _num(v):
    if isinstance(v,bool): return None
    try: x=float(v)
    except (TypeError,ValueError): return None
    return x if x==x and abs(x)!=float("inf") else None

def _registry():
    r=json.loads(REGISTRY_PATH.read_text())
    if r.get("version")!=APP_VERSION or r.get("schema")!=REGISTRY_SCHEMA: raise ValueError("advanced domain registry mismatch")
    return r

def registry_manifest():
    r=_registry(); return {"ok":True,"version":APP_VERSION,**deepcopy(r)}
def domain_profile(domain:str):
    d=next((x for x in _registry()["domains"] if x["domain_id"]==domain),None)
    if not d: raise ValueError(f"unknown advanced domain: {domain}")
    return {"ok":True,"version":APP_VERSION,"domain":deepcopy(d),"parity_level":"advanced-research-workspace"}

def law_analysis(request:Mapping[str,Any]):
    rows=[x for x in request.get("records",[]) if isinstance(x,Mapping)]
    authorities={}; bodies={}; countries=set(); subjects={}; binding=0
    for r in rows:
        a=_text(r.get("authority_level"),120) or "unclassified"; authorities[a]=authorities.get(a,0)+1
        b=_text(r.get("legal_body") or r.get("issuing_body"),240) or "unspecified"; bodies[b]=bodies.get(b,0)+1
        for c in r.get("countries") or ([r.get("country")] if r.get("country") else []): countries.add(str(c))
        for s in r.get("subjects") or []: subjects[str(s)]=subjects.get(str(s),0)+1
        if any(k in a.lower() for k in ("binding","treaty","resolution","judicial")) and "non" not in a.lower(): binding+=1
    core={"schema":"sc-site-intelligence-advanced-international-law-analysis/1.0","version":APP_VERSION,"record_count":len(rows),"authority_distribution":authorities,"legal_body_distribution":bodies,"country_count":len(countries),"top_subjects":sorted(subjects.items(),key=lambda x:(-x[1],x[0]))[:20],"binding_candidate_count":binding,"legal_conclusion":False,"automatic_authority_ranking":False,"human_legal_review_required":True}
    d=_digest(core); return {"ok":True,"version":APP_VERSION,"analysis":{**core,"analysis_digest":d}}

def economics_analysis(request:Mapping[str,Any]):
    rows=[x for x in request.get("records",[]) if isinstance(x,Mapping)]
    groups={}
    for r in rows:
        key=(str(r.get("indicator_code") or "unknown"),str(r.get("unit") or "unknown"),str(r.get("frequency") or "unknown"))
        g=groups.setdefault(key,{"indicator_code":key[0],"unit":key[1],"frequency":key[2],"values":[],"geographies":set(),"sources":set()})
        v=_num(r.get("value_number"));
        if v is not None:g["values"].append(v)
        if r.get("geography_code"):g["geographies"].add(str(r["geography_code"]))
        if r.get("source_id"):g["sources"].add(str(r["source_id"]))
    comps=[]
    for g in groups.values():
        vals=g.pop("values"); geos=sorted(g.pop("geographies")); sources=sorted(g.pop("sources"))
        comps.append({**g,"geographies":geos,"sources":sources,"numeric_count":len(vals),"mean":sum(vals)/len(vals) if vals else None,"direct_comparison_allowed":len(sources)<=1,"reason":"same-indicator-unit-frequency" if len(sources)<=1 else "multiple-sources-require-method-review"})
    core={"schema":"sc-site-intelligence-advanced-economics-analysis/1.0","version":APP_VERSION,"record_count":len(rows),"comparability_groups":sorted(comps,key=lambda x:x["indicator_code"]),"silent_unit_normalization":False,"silent_currency_conversion":False,"investment_advice":False,"causal_claims":False}
    d=_digest(core); return {"ok":True,"version":APP_VERSION,"analysis":{**core,"analysis_digest":d}}

def ocean_analysis(request:Mapping[str,Any]):
    rows=[x for x in request.get("observations",[]) if isinstance(x,Mapping)]
    vars={}; depth_bins={"surface":0,"upper-ocean":0,"mesopelagic":0,"deep":0,"unknown":0}
    for r in rows:
        var=_text(r.get("variable") or r.get("parameter"),160) or "unknown"; unit=_text(r.get("unit"),80) or "unknown"; key=f"{var}|{unit}"; v=_num(r.get("value"));
        bucket=vars.setdefault(key,{"variable":var,"unit":unit,"values":[],"source_ids":set()});
        if v is not None:bucket["values"].append(v)
        if r.get("source_id"):bucket["source_ids"].add(str(r["source_id"]))
        depth=_num(r.get("depth_m") or r.get("depth"))
        bin="unknown" if depth is None else "surface" if depth<10 else "upper-ocean" if depth<200 else "mesopelagic" if depth<1000 else "deep"; depth_bins[bin]+=1
    summaries=[]
    for g in vars.values():
        vals=g.pop("values"); src=sorted(g.pop("source_ids")); summaries.append({**g,"source_ids":src,"count":len(vals),"min":min(vals) if vals else None,"max":max(vals) if vals else None,"mean":sum(vals)/len(vals) if vals else None})
    core={"schema":"sc-site-intelligence-advanced-ocean-analysis/1.0","version":APP_VERSION,"observation_count":len(rows),"variable_summaries":sorted(summaries,key=lambda x:(x["variable"],x["unit"])),"depth_distribution":depth_bins,"automatic_interpolation":False,"automatic_anomaly_claim":False,"source_qc_preserved":True,"cross_system_tools":["water-column","seafloor","biodiversity","missions","hazards","human-activity","pollution","coastal-change","governance"]}
    d=_digest(core); return {"ok":True,"version":APP_VERSION,"analysis":{**core,"analysis_digest":d}}

def space_analysis(request:Mapping[str,Any]):
    rows=[x for x in request.get("records",[]) if isinstance(x,Mapping)]
    kinds={}; missions=set(); targets=set(); sources=set()
    for r in rows:
        k=_text(r.get("record_type") or r.get("type") or r.get("kind"),120) or "unknown"; kinds[k]=kinds.get(k,0)+1
        if r.get("mission_id") or r.get("mission"): missions.add(str(r.get("mission_id") or r.get("mission")))
        if r.get("target_id") or r.get("target"): targets.add(str(r.get("target_id") or r.get("target")))
        if r.get("source_id"): sources.add(str(r["source_id"]))
    core={"schema":"sc-site-intelligence-advanced-space-analysis/1.0","version":APP_VERSION,"record_count":len(rows),"record_type_distribution":kinds,"mission_count":len(missions),"target_count":len(targets),"source_count":len(sources),"mission_ids":sorted(missions)[:100],"target_ids":sorted(targets)[:100],"automatic_orbit_inference":False,"automatic_signal_authenticity":False,"automatic_habitability_claim":False,"cross_system_tools":["orbital-earth","planetary","astronomy","solar-system","exoplanets","seti","live-space"]}
    d=_digest(core); return {"ok":True,"version":APP_VERSION,"analysis":{**core,"analysis_digest":d}}

def parity_audit():
    r=_registry(); required={"evidence","comparison","scenario","provenance","research-handoff","export","diagnostics"}
    rows=[]
    for d in r["domains"]:
        have=set(d.get("advanced_capabilities") or []); missing=sorted(required-have)
        rows.append({"domain_id":d["domain_id"],"advanced":not missing,"missing":missing,"capability_count":len(have)})
    return {"ok":all(x["advanced"] for x in rows),"version":APP_VERSION,"required_capabilities":sorted(required),"domains":rows,"parity_target":"advanced-research-workspace"}

def research_context(request:Mapping[str,Any]):
    research=request.get("research_object")
    if not isinstance(research,Mapping):raise ValueError("research_object is required")
    v=validate_research_object(research)
    if not v["valid"]:raise ValueError("invalid research object")
    domain=_text(request.get("domain"),80); analysis=request.get("analysis") if isinstance(request.get("analysis"),Mapping) else {}
    core={"schema":"sc-site-intelligence-advanced-domain-research-context/1.0","version":APP_VERSION,"domain":domain,"research_object_id":research["research_object_id"],"research_digest":research["research_digest"],"analysis_digest":analysis.get("analysis_digest"),"research_object_mutated":False,"handoff_ready":True}
    d=_digest(core);return {"ok":True,"version":APP_VERSION,"research_context":{**core,"research_context_digest":d}}

def compatibility_manifest():
    return {"ok":True,"version":APP_VERSION,"legacy_economics_v220":"preserved-and-repaired","legacy_law_v230":"preserved-and-repaired","ocean_v4360":"preserved-and-advanced","science_space_v240":"preserved-and-advanced","wordpress_role":"public-site-launch-bridge"}
