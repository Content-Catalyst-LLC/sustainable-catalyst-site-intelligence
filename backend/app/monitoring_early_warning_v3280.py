"""Monitoring, digests, and early-warning operations for Site Intelligence v4.26.0.

The public contract is deterministic and review-oriented. It evaluates supplied public
records and source-state snapshots, explains every trigger, and never claims emergency
dispatch, automatic publication, individual tracking, or a hidden risk score.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from .version import APP_VERSION

SCHEMA = "sc-site-intelligence-monitoring-early-warning/1.0"
RELEASE_ID = f"site-intelligence-v{APP_VERSION}"
POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "monitoring_early_warning_policy_v3280.json"
OPS = {">", ">=", "<", "<=", "==", "!="}
_SECRET = re.compile(r"(?:password|secret|token|authorization|cookie|session|email|phone|user[_-]?id|person[_-]?id)", re.I)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _policy() -> dict[str, Any]:
    data = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if data.get("version") != APP_VERSION:
        raise ValueError("Monitoring policy version does not match application version.")
    return data


def _text(value: Any, limit: int = 1200) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value or "")).strip()[:limit]


def _items(value: Any, limit: int = 200) -> list[Any]:
    return list(value)[:limit] if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) else []


def _digest(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str).encode()).hexdigest()


def _scan(value: Any, path: str = "payload") -> list[str]:
    out: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            p = f"{path}.{key}"
            if _SECRET.search(str(key)):
                out.append(f"Individual, credential, or sensitive field is not allowed: {p}")
            out.extend(_scan(child, p))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            out.extend(_scan(child, f"{path}[{i}]"))
    return out


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    return n if math.isfinite(n) else None


def _compare(value: float, operator: str, threshold: float) -> bool:
    return {
        ">": value > threshold, ">=": value >= threshold, "<": value < threshold,
        "<=": value <= threshold, "==": value == threshold, "!=": value != threshold,
    }[operator]


def _area(raw: Mapping[str, Any], index: int) -> dict[str, Any]:
    bbox = raw.get("bbox") if isinstance(raw.get("bbox"), list) and len(raw.get("bbox")) == 4 else []
    return {
        "area_id": _text(raw.get("area_id") or raw.get("id") or f"area-{index+1}", 120),
        "label": _text(raw.get("label") or raw.get("name") or "Monitoring area", 220),
        "country": _text(raw.get("country") or raw.get("country_code"), 12).upper(),
        "region": _text(raw.get("region"), 160),
        "bbox": [float(x) for x in bbox if _number(x) is not None][:4],
        "resolution": _text(raw.get("resolution") or "public geographic area", 120),
        "individual_tracking": False,
    }


def _rule(raw: Mapping[str, Any], index: int) -> dict[str, Any]:
    operator = _text(raw.get("operator") or ">=", 3)
    if operator not in OPS:
        operator = ">="
    threshold = _number(raw.get("threshold"))
    return {
        "rule_id": _text(raw.get("rule_id") or raw.get("id") or f"rule-{index+1}", 120),
        "name": _text(raw.get("name") or raw.get("title") or f"Threshold rule {index+1}", 240),
        "watch_type": _text(raw.get("watch_type") or "indicator-threshold", 80),
        "indicator_id": _text(raw.get("indicator_id") or raw.get("metric"), 160),
        "country": _text(raw.get("country") or raw.get("country_code"), 12).upper(),
        "source_id": _text(raw.get("source_id"), 160),
        "operator": operator,
        "threshold": threshold,
        "unit": _text(raw.get("unit"), 80),
        "freshness_required": _text(raw.get("freshness_required"), 80),
    }


def _signal(raw: Mapping[str, Any], index: int) -> dict[str, Any]:
    countries = [_text(x, 12).upper() for x in _items(raw.get("countries"), 40) if _text(x, 12)]
    c = _text(raw.get("country") or raw.get("country_code"), 12).upper()
    if c and c not in countries:
        countries.append(c)
    out = {
        "signal_id": _text(raw.get("signal_id") or raw.get("record_id") or raw.get("id") or f"signal-{index+1}", 180),
        "title": _text(raw.get("title") or raw.get("name") or "Public signal", 320),
        "indicator_id": _text(raw.get("indicator_id") or raw.get("indicator_code") or raw.get("metric"), 160),
        "source_id": _text(raw.get("source_id") or raw.get("source"), 180),
        "countries": countries,
        "value": _number(raw.get("value") if "value" in raw else raw.get("value_number")),
        "unit": _text(raw.get("unit"), 80),
        "observed_at": _text(raw.get("observed_at") or raw.get("published_at") or raw.get("period"), 100),
        "retrieved_at": _text(raw.get("retrieved_at") or raw.get("captured_at"), 100),
        "freshness": _text(raw.get("freshness") or raw.get("truth_state") or "unknown", 80).lower(),
        "withdrawn": bool(raw.get("withdrawn", False)),
        "source_url": _text(raw.get("source_url") or raw.get("url"), 1200),
        "limitations": [_text(x, 500) for x in _items(raw.get("limitations"), 20) if _text(x, 500)],
    }
    out["fingerprint"] = _digest({k: v for k, v in out.items() if k != "fingerprint"})
    return out


class MonitoringEarlyWarningCenter:
    def __init__(self) -> None:
        self.policy = _policy()

    def schema(self) -> dict[str, Any]:
        return {
            "ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA,
            "contract": "monitoring-digests-and-early-warning-operations",
            "alert_states": list(self.policy["alert_states"]), "watch_types": list(self.policy["watch_types"]),
            "cadences": list(self.policy["cadences"]), "feed_formats": list(self.policy["feed_formats"]),
            "capabilities": ["saved watchlist contract", "indicator threshold evaluation", "geographic monitoring areas", "source-change detection", "freshness-change detection", "alert-state history normalization", "review-gated digest preview", "public feed contract", "modeled-warning distinction"],
            "persistent_scheduler_active": False, "human_review_required": True, "automatic_publication": False,
            "automatic_emergency_dispatch": False, "individual_tracking": False, "hidden_risk_score": False,
            "boundaries": list(self.policy["principles"]),
        }

    def watchlist(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        issues = _scan(request)
        if issues:
            raise ValueError("; ".join(issues[:5]))
        rules = [_rule(x, i) for i, x in enumerate(_items(request.get("rules"), 50)) if isinstance(x, Mapping)]
        areas = [_area(x, i) for i, x in enumerate(_items(request.get("areas"), 100)) if isinstance(x, Mapping)]
        cadence = _text(request.get("cadence") or "daily", 20).lower()
        if cadence not in self.policy["cadences"]:
            cadence = "daily"
        watchlist = {
            "watchlist_id": _text(request.get("watchlist_id") or request.get("id") or "watchlist-preview", 160),
            "title": _text(request.get("title") or "Site Intelligence watchlist", 280),
            "cadence": cadence, "countries": sorted({_text(x, 12).upper() for x in _items(request.get("countries"), 100) if _text(x, 12)}),
            "source_ids": sorted({_text(x, 160) for x in _items(request.get("source_ids"), 100) if _text(x, 160)}),
            "areas": areas, "rules": rules, "created_at": _text(request.get("created_at") or _now(), 100),
            "browser_or_export_persistence": True, "server_write_performed": False, "individual_tracking": False,
        }
        watchlist["fingerprint"] = _digest(watchlist)
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA, "contract": "watchlist-preview", "watchlist": watchlist}

    def evaluate(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        watch = self.watchlist(request.get("watchlist") if isinstance(request.get("watchlist"), Mapping) else request)["watchlist"]
        signals = [_signal(x, i) for i, x in enumerate(_items(request.get("signals"), 1000)) if isinstance(x, Mapping)]
        previous = [_signal(x, i) for i, x in enumerate(_items(request.get("previous_signals"), 1000)) if isinstance(x, Mapping)]
        previous_by_key = {(s["signal_id"], s["indicator_id"], s["source_id"]): s for s in previous}
        current_keys: set[tuple[str, str, str]] = set()
        alerts: list[dict[str, Any]] = []
        for rule in watch["rules"]:
            if rule["threshold"] is None:
                continue
            for signal in signals:
                if signal["value"] is None:
                    continue
                if rule["indicator_id"] and signal["indicator_id"] != rule["indicator_id"]:
                    continue
                if rule["source_id"] and signal["source_id"] != rule["source_id"]:
                    continue
                if rule["country"] and rule["country"] not in signal["countries"]:
                    continue
                if rule["freshness_required"] and signal["freshness"] != rule["freshness_required"]:
                    continue
                if not _compare(signal["value"], rule["operator"], float(rule["threshold"])):
                    continue
                key = (signal["signal_id"], signal["indicator_id"], signal["source_id"])
                current_keys.add(key)
                prior = previous_by_key.get(key)
                if signal["withdrawn"]:
                    state = "withdrawn"
                elif prior is None:
                    state = "new"
                elif prior["value"] != signal["value"] or prior["freshness"] != signal["freshness"]:
                    state = "changed"
                else:
                    state = "continuing"
                trigger = f"{signal['indicator_id'] or signal['title']} {rule['operator']} {rule['threshold']}{(' ' + rule['unit']) if rule['unit'] else ''}"
                alert = {
                    "alert_id": _digest({"rule": rule["rule_id"], "signal": signal["signal_id"], "state": state})[:24],
                    "state": state, "rule": rule, "signal": signal,
                    "trigger": trigger, "explanation": f"The supplied public record matched rule '{rule['name']}' because {trigger}.",
                    "freshness": signal["freshness"], "limitations": list(signal["limitations"]),
                    "source_alert": True, "modeled_warning": False, "operational_emergency_alert": False,
                    "automated_consequential_action": False,
                }
                alert["fingerprint"] = _digest(alert)
                alerts.append(alert)
        for key, prior in previous_by_key.items():
            if key in current_keys:
                continue
            alerts.append({
                "alert_id": _digest({"prior": prior["fingerprint"], "state": "resolved"})[:24], "state": "resolved",
                "rule": {}, "signal": prior, "trigger": "Previously observed threshold match is not present in the supplied current set.",
                "explanation": "Resolved means the supplied current evaluation no longer contains the previous match; it does not prove the real-world condition ended.",
                "freshness": prior["freshness"], "limitations": ["Resolution is evaluation-relative, not proof of real-world resolution."],
                "source_alert": True, "modeled_warning": False, "operational_emergency_alert": False, "automated_consequential_action": False,
                "fingerprint": _digest({"prior": prior["fingerprint"], "state": "resolved"}),
            })
        payload = {"alerts": alerts, "watchlist_fingerprint": watch["fingerprint"], "evaluated_at": _now()}
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA, "contract": "monitoring-evaluation", "alert_count": len(alerts), **payload, "human_review_required": True}

    def source_changes(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        issues = _scan(request)
        if issues:
            raise ValueError("; ".join(issues[:5]))
        previous = { _text(x.get("source_id"),160): dict(x) for x in _items(request.get("previous"), 200) if isinstance(x, Mapping) and _text(x.get("source_id"),160)}
        current = { _text(x.get("source_id"),160): dict(x) for x in _items(request.get("current"), 200) if isinstance(x, Mapping) and _text(x.get("source_id"),160)}
        rows=[]
        for source_id in sorted(set(previous)|set(current)):
            a,b=previous.get(source_id),current.get(source_id)
            if a is None: state="new"
            elif b is None: state="unavailable"
            else:
                keys=("schema_fingerprint","status","freshness","coverage_fingerprint")
                changed=[k for k in keys if _text(a.get(k),300)!=_text(b.get(k),300)]
                state="changed" if changed else "continuing"
            rows.append({"source_id":source_id,"state":state,"changed_fields": changed if a and b else [],"previous":{k:_text((a or {}).get(k),300) for k in ("schema_fingerprint","status","freshness","coverage_fingerprint")},"current":{k:_text((b or {}).get(k),300) for k in ("schema_fingerprint","status","freshness","coverage_fingerprint")},"publisher_outage_verified":False})
        return {"ok":True,"version":APP_VERSION,"schema":SCHEMA,"contract":"source-change-monitoring","changes":rows,"change_count":sum(1 for r in rows if r["state"]!="continuing"),"publisher_wide_outage_claimed":False}

    def warning_preview(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        score = _number(request.get("model_output"))
        threshold = _number(request.get("threshold"))
        active = score is not None and threshold is not None and score >= threshold
        warning = {
            "state": "active" if active else "not-triggered", "model_id": _text(request.get("model_id") or "unspecified-model", 160),
            "model_output": score, "threshold": threshold, "assumption_reference": _text(request.get("assumption_reference"), 400),
            "explanation": "A modeled output crossed the supplied review threshold." if active else "The supplied modeled output did not cross the supplied review threshold.",
            "modeled_warning": True, "source_alert": False, "probability_claimed": False,
            "operational_emergency_alert": False, "automatic_action": False, "human_review_required": True,
            "limitations": ["A modeled warning is an analytical signal, not a prediction certainty or emergency instruction."],
        }
        warning["fingerprint"] = _digest(warning)
        return {"ok":True,"version":APP_VERSION,"schema":SCHEMA,"contract":"modeled-warning-preview","warning":warning}

    def digest(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        alerts = [dict(x) for x in _items(request.get("alerts"), 1000) if isinstance(x, Mapping)]
        state_counts = {state: sum(1 for x in alerts if _text(x.get("state"),40)==state) for state in self.policy["alert_states"]}
        sources = sorted({_text((x.get("signal") or {}).get("source_id"),160) for x in alerts if isinstance(x.get("signal"), Mapping) and _text((x.get("signal") or {}).get("source_id"),160)})
        digest = {
            "digest_id": _text(request.get("digest_id") or f"digest-preview-{_digest(alerts)[:12]}", 160), "title": _text(request.get("title") or "Monitoring digest preview", 320),
            "status": "draft", "created_at": _now(), "alert_count": len(alerts), "state_counts": state_counts, "source_ids": sources,
            "items": alerts[:100], "human_review_required": True, "publication_allowed": False, "automatic_publication": False,
            "editorial_note": "Review evidence, freshness, limitations, and alert-state transitions before publication.",
        }
        digest["fingerprint"] = _digest(digest)
        return {"ok":True,"version":APP_VERSION,"schema":SCHEMA,"contract":"monitoring-digest-preview","digest":digest}

    def feed_contract(self) -> dict[str, Any]:
        return {"ok":True,"version":APP_VERSION,"schema":SCHEMA,"contract":"reviewed-monitoring-feed-contract","formats":list(self.policy["feed_formats"]),"published_items_must_be_human_approved":True,"subscriber_profile_required":False,"tracking_required":False,"automatic_publication":False}


_CENTER = MonitoringEarlyWarningCenter()

def public_monitoring_operations() -> dict[str, Any]: return _CENTER.schema()
def public_watchlist_preview(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _CENTER.watchlist(request)
def public_monitoring_evaluation(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _CENTER.evaluate(request)
def public_source_change_monitoring(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _CENTER.source_changes(request)
def public_modeled_warning_preview(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _CENTER.warning_preview(request)
def public_monitoring_digest_preview(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _CENTER.digest(request)
def public_monitoring_feed_contract() -> dict[str, Any]: return _CENTER.feed_contract()
