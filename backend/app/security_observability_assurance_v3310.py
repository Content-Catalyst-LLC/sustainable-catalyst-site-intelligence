from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .config import Settings

RELEASE_VERSION = "4.11.0"
CONTRACT = "security-observability-performance-scale-assurance"
ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "backend/data/security_observability_performance_policy_v3310.json"

def _policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))

def _digest(value: Any) -> str:
    raw=json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    return hashlib.sha256(raw).hexdigest()

def _assets() -> list[Path]:
    base=ROOT / "backend/public_app/assets"
    return [p for p in base.rglob("*") if p.is_file()]

def public_security_observability_assurance(settings: Settings) -> dict[str, Any]:
    p=_policy()
    summary={
        "production_admin_auth":p["security"]["production_admin_auth"],
        "default_token_allowed":p["security"]["production_default_token_allowed"],
        "visitor_ip_persistence":p["security"]["visitor_ip_persistence"],
        "persistent_visitor_profiles":p["observability"]["persistent_visitor_profiles"],
        "hash_pinning_claimed":p["supply_chain"]["hash_pinning_claimed"],
        "public_embeds_enabled":settings.public_embeds_enabled,
    }
    return {"ok":True,"version":RELEASE_VERSION,"contract":CONTRACT,"summary":summary,"boundaries":p["boundaries"],"assurance_sha256":_digest({"summary":summary,"policy":p})}

def public_security_posture(settings: Settings) -> dict[str, Any]:
    p=_policy(); token_configured=bool(settings.api_token and settings.api_token != "dev-token-change-me")
    origins=[o for o in settings.cors_origin_list if o.startswith(("http://","https://"))]
    return {
      "ok":True,"version":RELEASE_VERSION,"production_fail_closed":True,
      "production_token_configured":token_configured if settings.environment=="production" else None,
      "default_development_token_rejected_in_production":True,
      "admin_rate_limit":{"limit":settings.production_admin_rate_limit,"window_seconds":settings.production_admin_rate_window_seconds,"key":"token-fingerprint","distributed":False},
      "cors":{"origins":origins,"wildcard_origin":False,"credentials":True,"methods":["GET","POST","OPTIONS"],"headers":["Accept","Content-Type","Cache-Control","Pragma","X-SC-Intelligence-Token"]},
      "required_headers":p["security"]["required_headers"],"csp":p["security"]["csp"],
      "external_penetration_test_claimed":False,"compliance_certification_claimed":False
    }

def public_observability_posture() -> dict[str, Any]:
    p=_policy()
    return {"ok":True,"version":RELEASE_VERSION,"dimensions":p["observability"]["dimensions"],"request_timing_header":p["observability"]["request_timing_header"],"persistent_visitor_profiles":False,"visitor_ip_storage":False,"public_diagnostics":"aggregate-contract-only","trace_correlation":"response-local","limitations":["No distributed tracing backend is claimed.","Upstream provider health is reported separately from local runtime health."]}

def public_performance_budget() -> dict[str, Any]:
    p=_policy(); budgets=p["performance_budgets"]
    assets=_assets(); js=[x for x in assets if x.suffix==".js"]; css=[x for x in assets if x.suffix==".css"]
    observed={
      "javascript_files":len(js),"css_files":len(css),
      "largest_javascript_asset_bytes":max((x.stat().st_size for x in js),default=0),
      "largest_css_asset_bytes":max((x.stat().st_size for x in css),default=0),
      "total_first_party_javascript_bytes":sum(x.stat().st_size for x in js),
      "total_first_party_css_bytes":sum(x.stat().st_size for x in css),
    }
    checks={k:{"observed":observed[k],"budget":budgets[k],"pass":observed[k]<=budgets[k]} for k in observed if k in budgets}
    return {"ok":all(v["pass"] for v in checks.values()),"version":RELEASE_VERSION,"budgets":budgets,"observed":observed,"checks":checks,"device_or_network_guarantee":False}

def public_rate_limit_preview(payload: dict[str, Any], settings: Settings) -> dict[str, Any]:
    requests=max(0,min(int(payload.get("requests",0) or 0),100000)); window=max(1,int(payload.get("window_seconds",settings.production_admin_rate_window_seconds) or 1));
    configured=settings.production_admin_rate_limit; normalized=round(requests * settings.production_admin_rate_window_seconds / window,3)
    allowed=normalized<=configured
    return {"ok":True,"version":RELEASE_VERSION,"preview":True,"requests":requests,"window_seconds":window,"normalized_requests_per_configured_window":normalized,"configured_limit":configured,"allowed_under_single_process_projection":allowed,"distributed_enforcement":False,"write_performed":False}

def public_supply_chain_posture() -> dict[str, Any]:
    p=_policy(); reqs=[]
    for name in ("backend/requirements.txt","backend/requirements-dev.txt"):
        path=ROOT/name
        for line in path.read_text().splitlines():
            line=line.strip()
            if line and not line.startswith("#"): reqs.append(line)
    exact=sum("==" in r for r in reqs); ranged=sum(any(op in r for op in (">=","<=","<",">","~=")) for r in reqs)
    return {"ok":True,"version":RELEASE_VERSION,"requirements":len(reqs),"exact_pins":exact,"version_constrained":ranged,"hash_pinning_claimed":False,"release_checks":["pip check","secret-pattern scan","immutable SHA-256 manifest","Python/JavaScript/PHP syntax validation"],"automatic_dependency_update":False,"policy":p["supply_chain"]}

def public_post_deploy_smoke_preview(payload: dict[str, Any]) -> dict[str, Any]:
    commit=str(payload.get("commit","expected-commit"))[:80]; release=str(payload.get("release",RELEASE_VERSION))[:40]
    checks=["release-gate identity","app shell 200","security headers","country catalog","Data Truth","record provenance","control plane","route soak","service-worker lifecycle","WordPress iframe isolation"]
    plan={"release":release,"commit":commit,"checks":checks,"network_requests_performed":False,"deployment_mutated":False,"human_review_required_for_failure":True}
    return {"ok":True,"version":RELEASE_VERSION,"preview":plan,"preview_sha256":_digest(plan)}
