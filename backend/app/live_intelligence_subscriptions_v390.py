"""Governed signal subscriptions, watchlists, alerts, and digest handoffs.

Site Intelligence v3.11.0 connects the canonical Live Intelligence signal
contract to reusable watchlists and scheduled review workflows. It deliberately
does not store subscriber profiles, send email, call webhooks, or automatically
publish alerts. Delivery remains provider-neutral and human-controlled.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from .config import Settings
from .live_intelligence_gateway_v370 import SIGNAL_FAMILY_REGISTRY
from .live_intelligence_surfaces_v380 import SURFACE_REGISTRY, normalize_surface_id
from .version import APP_VERSION

POLICY_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-subscription-policy/1.0"
WATCHLIST_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-watchlist/1.0"
ALERT_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-alert/1.0"
DIGEST_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-subscription-digest/1.0"
HANDOFF_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-delivery-handoff/1.0"

ALLOWED_CADENCES = ("manual", "hourly", "daily", "weekly")
ALLOWED_VISIBILITY = ("private", "public")
ALLOWED_MATCH_MODES = ("all", "any")
ALLOWED_DELIVERY_MODES = ("public_feed", "digest_export", "communications_handoff")
ALLOWED_RULE_TYPES = (
    "signal_id", "signal_family", "source_id", "freshness_state", "destination_type",
    "geography_scope", "geography_code", "numeric_above", "numeric_below", "text_contains",
)
DENIED_IDENTITY_FIELDS = {
    "subscriber", "subscriber_id", "subscriber_email", "email", "email_address", "phone",
    "phone_number", "name", "full_name", "user", "user_id", "account_id", "session_id",
    "cookie", "ip", "ip_address", "user_agent", "referrer", "recipient", "recipients",
    "mailing_list", "contact_id", "profile", "personalization", "metadata",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None = None) -> str:
    return (value or _utc_now()).astimezone(timezone.utc).isoformat()


def _parse(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _safe_text(value: Any, limit: int = 300) -> str:
    return " ".join(str(value or "").split())[:limit]


def _safe_id(value: Any, prefix: str = "item") -> str:
    text = _safe_text(value, 160).lower()
    text = re.sub(r"[^a-z0-9._:-]+", "-", text).strip("-._:")
    return text or f"{prefix}:{uuid4().hex[:16]}"


def _safe_url(value: Any) -> str:
    text = str(value or "").strip()
    return text[:1200] if text.startswith(("https://", "http://", "/")) else ""


def _resolve(value: str) -> Path:
    return Path(value).expanduser()


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _read_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except (FileNotFoundError, OSError):
        return []
    output: list[dict[str, Any]] = []
    for line in lines:
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(row, dict):
            output.append(row)
    return output


def _append(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(record), sort_keys=True, ensure_ascii=False) + "\n")


def _latest(path: Path, key: str, limit: int) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(path, limit):
        value = _safe_text(row.get(key), 180)
        if value:
            latest[value] = row
    return list(latest.values())


def _reject_identity_payload(value: Any, path: str = "request") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in DENIED_IDENTITY_FIELDS:
                raise ValueError(f"{path}.{key} is not accepted; subscriber identities and recipient profiles are outside Site Intelligence.")
            _reject_identity_payload(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_identity_payload(child, f"{path}[{index}]")


def _list(value: Any, *, maximum: int, item_limit: int = 120) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    output: list[str] = []
    for item in value[:maximum]:
        text = _safe_text(item, item_limit)
        if text and text not in output:
            output.append(text)
    return output


def _signal_numeric(signal: Mapping[str, Any]) -> float | None:
    for key in ("numeric_value", "value_number", "magnitude", "score"):
        value = signal.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    value = str(signal.get("formatted_value") or signal.get("value") or "")
    match = re.search(r"[-+]?\d+(?:\.\d+)?", value.replace(",", ""))
    try:
        return float(match.group(0)) if match else None
    except (TypeError, ValueError):
        return None


def _rule_value(rule: Mapping[str, Any]) -> Any:
    return rule.get("value") if "value" in rule else rule.get("threshold")


def validate_rule(source: Mapping[str, Any], index: int = 0) -> dict[str, Any]:
    rule_type = _safe_text(source.get("type"), 60).lower()
    if rule_type not in ALLOWED_RULE_TYPES:
        raise ValueError(f"Unsupported watchlist rule type at index {index}: {rule_type or 'missing'}.")
    rule_id = _safe_id(source.get("rule_id") or f"rule:{index + 1}", "rule")
    value = _rule_value(source)
    if rule_type in {"numeric_above", "numeric_below"}:
        try:
            normalized: Any = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Rule {rule_id} requires a numeric threshold.") from exc
    else:
        normalized = _safe_text(value, 180)
        if not normalized:
            raise ValueError(f"Rule {rule_id} requires a value.")
    return {
        "rule_id": rule_id,
        "type": rule_type,
        "value": normalized,
        "label": _safe_text(source.get("label") or rule_type.replace("_", " ").title(), 160),
    }


def signal_matches_rule(signal: Mapping[str, Any], rule: Mapping[str, Any]) -> bool:
    rule_type = str(rule.get("type") or "")
    expected = rule.get("value")
    if rule_type == "signal_id":
        return _safe_text(signal.get("signal_id"), 180) == str(expected)
    if rule_type == "signal_family":
        return _safe_text(signal.get("signal_family"), 80) == str(expected)
    if rule_type == "source_id":
        return _safe_text(signal.get("feed_id") or signal.get("source_id"), 120) == str(expected)
    if rule_type == "freshness_state":
        return _safe_text(signal.get("freshness_state"), 60) == str(expected)
    if rule_type == "destination_type":
        primary = signal.get("primary_destination") if isinstance(signal.get("primary_destination"), Mapping) else {}
        return _safe_text(signal.get("destination_type") or primary.get("type"), 80) == str(expected)
    if rule_type == "geography_scope":
        geography = signal.get("geography") if isinstance(signal.get("geography"), Mapping) else {}
        return _safe_text(geography.get("scope"), 60) == str(expected)
    if rule_type == "geography_code":
        geography = signal.get("geography") if isinstance(signal.get("geography"), Mapping) else {}
        observed = _safe_text(geography.get("country_code") or signal.get("country_code"), 20).upper()
        return observed == str(expected).upper()
    if rule_type in {"numeric_above", "numeric_below"}:
        observed = _signal_numeric(signal)
        if observed is None:
            return False
        threshold = float(expected)
        return observed > threshold if rule_type == "numeric_above" else observed < threshold
    if rule_type == "text_contains":
        haystack = " ".join(_safe_text(signal.get(key), 800) for key in ("label", "short_label", "value", "formatted_value", "detail", "source_name"))
        return str(expected).lower() in haystack.lower()
    return False


def signal_matches_watchlist(signal: Mapping[str, Any], watchlist: Mapping[str, Any]) -> tuple[bool, list[str]]:
    rules = [rule for rule in watchlist.get("rules", []) if isinstance(rule, Mapping)]
    if not rules:
        return False, []
    matched = [str(rule.get("rule_id") or "") for rule in rules if signal_matches_rule(signal, rule)]
    mode = str(watchlist.get("match_mode") or "all")
    return ((len(matched) == len(rules)) if mode == "all" else bool(matched)), matched


def subscription_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "principle": "Watch public signals without turning Site Intelligence into a subscriber database or autonomous alerting authority.",
        "supported_cadences": list(ALLOWED_CADENCES),
        "supported_delivery_modes": list(ALLOWED_DELIVERY_MODES),
        "supported_rule_types": list(ALLOWED_RULE_TYPES),
        "supported_surfaces": list(SURFACE_REGISTRY),
        "supported_signal_families": list(SIGNAL_FAMILY_REGISTRY),
        "public_routes": {
            "catalog": "/public/live-intelligence/subscriptions/catalog",
            "alerts": "/public/live-intelligence/subscriptions/alerts",
            "digests": "/public/live-intelligence/subscriptions/digests",
            "preferences": "/public/live-intelligence/subscriptions/preferences",
        },
        "boundaries": {
            "subscriber_profiles_stored": False,
            "email_sent_by_site_intelligence": False,
            "webhooks_called_by_site_intelligence": False,
            "automatic_publication": False,
            "automated_emergency_authority": False,
            "human_review_required_for_public_alerts": True,
            "provider_neutral_delivery_handoffs": True,
            "advertising_or_affiliate_delivery": False,
        },
    }


def preference_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "preference_fields": {
            "watchlist_id": "Choose a published public watchlist.",
            "cadence": list(ALLOWED_CADENCES),
            "delivery_mode": list(ALLOWED_DELIVERY_MODES),
        },
        "storage": "Preferences are not accepted or stored by this Site Intelligence endpoint.",
        "handoff": "A separate communications service may consume an approved provider-neutral manifest and manage consent, recipients, unsubscribe controls, and delivery.",
        "subscriber_profiles_stored": False,
    }


class LiveIntelligenceSubscriptionCenter:
    def __init__(
        self,
        settings: Settings,
        *,
        signal_loader: Callable[[dict[str, Any]], Mapping[str, Any]] | None = None,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.settings = settings
        self.signal_loader = signal_loader
        self.now_fn = now_fn
        self.watchlists_path = _resolve(settings.live_intelligence_watchlists_path)
        self.evaluations_path = _resolve(settings.live_intelligence_subscription_evaluations_path)
        self.alerts_path = _resolve(settings.live_intelligence_subscription_alerts_path)
        self.digests_path = _resolve(settings.live_intelligence_subscription_digests_path)
        self.handoffs_path = _resolve(settings.live_intelligence_subscription_handoffs_path)
        self.max_records = int(settings.live_intelligence_subscriptions_max_records)
        self.max_rules = int(settings.live_intelligence_subscriptions_max_rules)
        self.max_alerts_per_run = int(settings.live_intelligence_subscriptions_max_alerts_per_run)
        self.dedupe_hours = int(settings.live_intelligence_subscriptions_dedupe_hours)

    def _next_due(self, cadence: str, now: datetime) -> str:
        delta = {"hourly": timedelta(hours=1), "daily": timedelta(days=1), "weekly": timedelta(days=7)}.get(cadence)
        return _iso(now + delta) if delta else ""

    def watchlists(self, public: bool = False) -> list[dict[str, Any]]:
        rows = [row for row in _latest(self.watchlists_path, "watchlist_id", self.max_records) if not row.get("deleted")]
        if public:
            rows = [row for row in rows if row.get("enabled") and row.get("visibility") == "public" and row.get("review_status") == "approved"]
            rows = [self._public_watchlist(row) for row in rows]
        return sorted(rows, key=lambda row: (str(row.get("title") or ""), str(row.get("watchlist_id") or "")))

    def _watchlist(self, watchlist_id: str, *, public: bool = False) -> dict[str, Any]:
        target = _safe_id(watchlist_id, "watchlist")
        for row in self.watchlists(public=public):
            if row.get("watchlist_id") == target:
                return row
        raise KeyError(target)

    def _public_watchlist(self, row: Mapping[str, Any]) -> dict[str, Any]:
        watchlist_id = str(row.get("watchlist_id") or "")
        return {
            "schema": WATCHLIST_SCHEMA_VERSION,
            "version": APP_VERSION,
            "watchlist_id": watchlist_id,
            "title": row.get("title") or "",
            "summary": row.get("summary") or "",
            "surface": row.get("surface") or "homepage",
            "channel": row.get("channel") or "global",
            "families": list(row.get("families") or []),
            "cadence": row.get("cadence") or "manual",
            "match_mode": row.get("match_mode") or "all",
            "rule_count": len(row.get("rules") or []),
            "rule_summary": [rule.get("label") or rule.get("type") for rule in row.get("rules", []) if isinstance(rule, Mapping)],
            "delivery_modes": list(row.get("delivery_modes") or []),
            "last_evaluated_at": row.get("last_evaluated_at") or "",
            "next_due_at": row.get("next_due_at") or "",
            "feed_urls": {
                "json": f"/public/live-intelligence/subscriptions/watchlists/{watchlist_id}/feed?format=json",
                "rss": f"/public/live-intelligence/subscriptions/watchlists/{watchlist_id}/feed?format=rss",
                "atom": f"/public/live-intelligence/subscriptions/watchlists/{watchlist_id}/feed?format=atom",
            },
            "automatic_publication": False,
            "subscriber_profiles_stored": False,
        }

    def save_watchlist(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        title = _safe_text(request.get("title"), 240)
        if not title:
            raise ValueError("title is required.")
        watchlist_id = _safe_id(request.get("watchlist_id") or f"watchlist:{uuid4().hex[:16]}", "watchlist")
        previous = next((row for row in self.watchlists(False) if row.get("watchlist_id") == watchlist_id), {})
        cadence = _safe_text(request.get("cadence") or previous.get("cadence") or "manual", 20).lower()
        visibility = _safe_text(request.get("visibility") or previous.get("visibility") or "private", 20).lower()
        match_mode = _safe_text(request.get("match_mode") or previous.get("match_mode") or "all", 12).lower()
        if cadence not in ALLOWED_CADENCES:
            raise ValueError("Unsupported cadence.")
        if visibility not in ALLOWED_VISIBILITY:
            raise ValueError("Unsupported visibility.")
        if match_mode not in ALLOWED_MATCH_MODES:
            raise ValueError("Unsupported match_mode.")
        surface = normalize_surface_id(request.get("surface") or previous.get("surface") or "homepage")
        source_rules = request.get("rules") if isinstance(request.get("rules"), list) else previous.get("rules", [])
        if not source_rules:
            raise ValueError("At least one watchlist rule is required.")
        if len(source_rules) > self.max_rules:
            raise ValueError(f"A watchlist may contain at most {self.max_rules} rules.")
        rules = [validate_rule(rule, index) for index, rule in enumerate(source_rules) if isinstance(rule, Mapping)]
        if not rules:
            raise ValueError("At least one valid watchlist rule is required.")
        families = [family for family in _list(request.get("families") or previous.get("families", []), maximum=16, item_limit=80) if family in SIGNAL_FAMILY_REGISTRY]
        modes = [mode for mode in _list(request.get("delivery_modes") or previous.get("delivery_modes", ["public_feed"]), maximum=3, item_limit=40) if mode in ALLOWED_DELIVERY_MODES]
        review_status = "private"
        approved_by = ""
        approval_reason = ""
        if visibility == "public":
            approved = bool(request.get("human_approved", previous.get("review_status") == "approved"))
            approved_by = _safe_text(request.get("approved_by") or previous.get("approved_by"), 160)
            approval_reason = _safe_text(request.get("approval_reason") or previous.get("approval_reason"), 600)
            if not approved or not approved_by or not approval_reason:
                raise ValueError("Public watchlists require human_approved=true, approved_by, and approval_reason.")
            review_status = "approved"
        now = self.now_fn().astimezone(timezone.utc)
        record = {
            "schema": WATCHLIST_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "watchlist_id": watchlist_id,
            "title": title,
            "summary": _safe_text(request.get("summary") or previous.get("summary"), 2000),
            "enabled": bool(request.get("enabled", previous.get("enabled", True))),
            "visibility": visibility,
            "review_status": review_status,
            "approved_by": approved_by,
            "approval_reason": approval_reason,
            "surface": surface,
            "channel": _safe_text(request.get("channel") or previous.get("channel") or SURFACE_REGISTRY[surface]["default_channel"], 100),
            "region": _safe_text(request.get("region") or previous.get("region"), 100),
            "country": _safe_text(request.get("country") or previous.get("country"), 100),
            "families": families,
            "rules": rules,
            "match_mode": match_mode,
            "cadence": cadence,
            "delivery_modes": modes or ["public_feed"],
            "max_alerts_per_run": max(1, min(int(request.get("max_alerts_per_run", previous.get("max_alerts_per_run", self.max_alerts_per_run))), self.max_alerts_per_run)),
            "created_at": previous.get("created_at") or _iso(now),
            "updated_at": _iso(now),
            "last_evaluated_at": previous.get("last_evaluated_at") or "",
            "next_due_at": previous.get("next_due_at") or self._next_due(cadence, now),
            "automatic_publication": False,
            "automatic_delivery": False,
            "subscriber_profiles_stored": False,
            "email_delivery": False,
            "webhook_delivery": False,
            "emergency_dispatch": False,
        }
        record["watchlist_sha256"] = _canonical_digest({key: value for key, value in record.items() if key != "watchlist_sha256"})
        _append(self.watchlists_path, record)
        return {"ok": True, "version": APP_VERSION, "watchlist": record}

    def due_watchlists(self, at: datetime | None = None) -> list[dict[str, Any]]:
        now = (at or self.now_fn()).astimezone(timezone.utc)
        output = []
        for row in self.watchlists(False):
            if not row.get("enabled") or row.get("cadence") == "manual":
                continue
            due = _parse(row.get("next_due_at"))
            if due is None or due <= now:
                output.append(row)
        return output

    def _recent_fingerprints(self, since: datetime) -> set[str]:
        output = set()
        for row in _read_jsonl(self.alerts_path, self.max_records):
            created = _parse(row.get("created_at"))
            if row.get("fingerprint") and created and created >= since:
                output.add(str(row["fingerprint"]))
        return output

    def _signal_snapshot(self, signal: Mapping[str, Any]) -> dict[str, Any]:
        geography = signal.get("geography") if isinstance(signal.get("geography"), Mapping) else {}
        primary = signal.get("primary_destination") if isinstance(signal.get("primary_destination"), Mapping) else {}
        return {
            "signal_id": _safe_text(signal.get("signal_id"), 180),
            "label": _safe_text(signal.get("label") or signal.get("short_label"), 160),
            "value": _safe_text(signal.get("formatted_value") or signal.get("value"), 240),
            "numeric_value": _signal_numeric(signal),
            "signal_family": _safe_text(signal.get("signal_family"), 80),
            "source_id": _safe_text(signal.get("feed_id") or signal.get("source_id"), 120),
            "source_name": _safe_text(signal.get("source_name"), 180),
            "source_url": _safe_url(signal.get("source_url")),
            "freshness_state": _safe_text(signal.get("freshness_state"), 60),
            "observed_at": _safe_text(signal.get("observed_at"), 80),
            "updated_at": _safe_text(signal.get("updated_at"), 80),
            "geography": {
                "scope": _safe_text(geography.get("scope"), 40),
                "label": _safe_text(geography.get("label"), 160),
                "country_code": _safe_text(geography.get("country_code"), 20),
            },
            "primary_destination": {
                "type": _safe_text(primary.get("type"), 80),
                "label": _safe_text(primary.get("label"), 160),
                "url": _safe_url(primary.get("url")),
            },
            "context_url": _safe_url(signal.get("context_view_url") or signal.get("context_url")),
            "evidence_url": _safe_url(signal.get("evidence_url")),
        }

    def evaluate_watchlist(self, watchlist_id: str, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = request or {}
        _reject_identity_payload(request)
        watchlist = self._watchlist(watchlist_id)
        dry_run = bool(request.get("dry_run", False))
        if isinstance(request.get("signals"), list):
            signals = [dict(item) for item in request["signals"] if isinstance(item, Mapping)]
            delivery_state = "provided"
        else:
            if self.signal_loader is None:
                raise ValueError("No canonical Live Intelligence signal loader is configured.")
            payload = self.signal_loader(watchlist)
            signals = [dict(item) for item in payload.get("signals", []) if isinstance(item, Mapping)]
            delivery_state = _safe_text(payload.get("delivery_state") or payload.get("origin_state") or "canonical_feed", 80)
        matches: list[tuple[dict[str, Any], list[str]]] = []
        for signal in signals:
            matched, rule_ids = signal_matches_watchlist(signal, watchlist)
            if matched:
                matches.append((signal, rule_ids))
        now = self.now_fn().astimezone(timezone.utc)
        known = self._recent_fingerprints(now - timedelta(hours=self.dedupe_hours))
        created: list[dict[str, Any]] = []
        duplicates = 0
        cap = int(watchlist.get("max_alerts_per_run") or self.max_alerts_per_run)
        for signal, rule_ids in matches[:cap]:
            snapshot = self._signal_snapshot(signal)
            fingerprint = _canonical_digest({
                "watchlist_id": watchlist["watchlist_id"],
                "signal_id": snapshot["signal_id"],
                "value": snapshot["value"],
                "freshness": snapshot["freshness_state"],
                "rules": sorted(rule_ids),
            })
            if fingerprint in known:
                duplicates += 1
                continue
            alert = {
                "schema": ALERT_SCHEMA_VERSION,
                "release_version": APP_VERSION,
                "alert_id": f"alert:{uuid4().hex[:20]}",
                "watchlist_id": watchlist["watchlist_id"],
                "watchlist_title": watchlist["title"],
                "signal": snapshot,
                "matched_rule_ids": rule_ids,
                "fingerprint": fingerprint,
                "status": "pending_review",
                "visibility": watchlist.get("visibility") or "private",
                "created_at": _iso(now),
                "reviewed_at": "",
                "reviewed_by": "",
                "review_reason": "",
                "published": False,
                "automatic_publication": False,
                "emergency_dispatch": False,
            }
            alert["alert_sha256"] = _canonical_digest({key: value for key, value in alert.items() if key != "alert_sha256"})
            created.append(alert)
            known.add(fingerprint)
            if not dry_run:
                _append(self.alerts_path, alert)
        evaluation = {
            "schema": "sc-site-intelligence-live-intelligence-watchlist-evaluation/1.0",
            "release_version": APP_VERSION,
            "evaluation_id": f"evaluation:{uuid4().hex[:20]}",
            "watchlist_id": watchlist["watchlist_id"],
            "evaluated_at": _iso(now),
            "signal_count": len(signals),
            "match_count": len(matches),
            "created_alert_count": len(created),
            "duplicate_count": duplicates,
            "dry_run": dry_run,
            "delivery_state": delivery_state,
            "automatic_publication": False,
        }
        if not dry_run:
            _append(self.evaluations_path, evaluation)
            updated = dict(watchlist)
            updated["updated_at"] = _iso(now)
            updated["last_evaluated_at"] = _iso(now)
            updated["next_due_at"] = self._next_due(str(watchlist.get("cadence") or "manual"), now)
            updated["last_evaluation"] = {
                "evaluation_id": evaluation["evaluation_id"],
                "signal_count": len(signals),
                "match_count": len(matches),
                "created_alert_count": len(created),
            }
            updated["watchlist_sha256"] = _canonical_digest({key: value for key, value in updated.items() if key != "watchlist_sha256"})
            _append(self.watchlists_path, updated)
        return {"ok": True, "version": APP_VERSION, "evaluation": evaluation, "alerts": created}

    def alerts(self, public: bool = False, *, watchlist_id: str = "", limit: int = 200) -> list[dict[str, Any]]:
        rows = [row for row in _latest(self.alerts_path, "alert_id", self.max_records) if not row.get("deleted")]
        if watchlist_id:
            rows = [row for row in rows if row.get("watchlist_id") == _safe_id(watchlist_id, "watchlist")]
        if public:
            rows = [row for row in rows if row.get("published") is True and row.get("status") == "approved" and row.get("visibility") == "public"]
            rows = [self._public_alert(row) for row in rows]
        return sorted(rows, key=lambda row: str(row.get("created_at") or ""), reverse=True)[:max(1, min(int(limit), 500))]

    def _public_alert(self, row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "schema": ALERT_SCHEMA_VERSION,
            "version": APP_VERSION,
            "alert_id": row.get("alert_id") or "",
            "watchlist_id": row.get("watchlist_id") or "",
            "watchlist_title": row.get("watchlist_title") or "",
            "signal": deepcopy(row.get("signal") or {}),
            "created_at": row.get("created_at") or "",
            "published_at": row.get("published_at") or "",
            "reviewed": True,
            "automatic_publication": False,
            "interpretation": "A human-reviewed match against a public watchlist. It is not an emergency notification or a claim that no unreported change exists.",
        }

    def review_alert(self, alert_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        decision = _safe_text(request.get("decision"), 20).lower()
        reviewer = _safe_text(request.get("reviewed_by"), 160)
        reason = _safe_text(request.get("reason"), 1000)
        if decision not in {"approve", "reject"}:
            raise ValueError("decision must be approve or reject.")
        if not reviewer or not reason:
            raise ValueError("reviewed_by and reason are required.")
        current = next((row for row in self.alerts(False, limit=500) if row.get("alert_id") == _safe_id(alert_id, "alert")), None)
        if current is None:
            raise KeyError(alert_id)
        now = self.now_fn().astimezone(timezone.utc)
        updated = dict(current)
        updated.update({
            "status": "approved" if decision == "approve" else "rejected",
            "reviewed_at": _iso(now),
            "reviewed_by": reviewer,
            "review_reason": reason,
            "published": decision == "approve" and current.get("visibility") == "public",
            "published_at": _iso(now) if decision == "approve" and current.get("visibility") == "public" else "",
            "automatic_publication": False,
        })
        updated["alert_sha256"] = _canonical_digest({key: value for key, value in updated.items() if key != "alert_sha256"})
        _append(self.alerts_path, updated)
        return {"ok": True, "version": APP_VERSION, "alert": updated}

    def generate_digest(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        title = _safe_text(request.get("title"), 260)
        if not title:
            raise ValueError("title is required.")
        watchlist_ids = _list(request.get("watchlist_ids"), maximum=100, item_limit=180)
        alert_ids = set(_list(request.get("alert_ids"), maximum=500, item_limit=180))
        candidates = self.alerts(False, limit=1000)
        selected = [row for row in candidates if row.get("status") == "approved"]
        if watchlist_ids:
            selected = [row for row in selected if row.get("watchlist_id") in watchlist_ids]
        if alert_ids:
            selected = [row for row in selected if row.get("alert_id") in alert_ids]
        visibility = _safe_text(request.get("visibility") or "private", 20).lower()
        if visibility not in ALLOWED_VISIBILITY:
            raise ValueError("visibility must be private or public.")
        if visibility == "public":
            selected = [
                row for row in selected
                if row.get("visibility") == "public" and row.get("published") is True
            ]
        limit = max(1, min(int(request.get("limit", 50)), 200))
        selected = selected[:limit]
        if not selected:
            raise ValueError("No approved alerts matched the digest request.")
        now = self.now_fn().astimezone(timezone.utc)
        digest = {
            "schema": DIGEST_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "digest_id": f"digest:{uuid4().hex[:20]}",
            "title": title,
            "summary": _safe_text(request.get("summary"), 3000),
            "period": _safe_text(request.get("period") or "manual", 40),
            "visibility": visibility,
            "alert_count": len(selected),
            "alerts": [self._public_alert(row) if row.get("visibility") == "public" else {
                "alert_id": row.get("alert_id"), "watchlist_id": row.get("watchlist_id"),
                "watchlist_title": row.get("watchlist_title"), "signal": deepcopy(row.get("signal") or {}),
                "created_at": row.get("created_at"),
            } for row in selected],
            "status": "draft",
            "created_at": _iso(now),
            "reviewed_at": "",
            "reviewed_by": "",
            "review_reason": "",
            "published": False,
            "automatic_publication": False,
            "automatic_delivery": False,
        }
        digest["digest_sha256"] = _canonical_digest({key: value for key, value in digest.items() if key != "digest_sha256"})
        _append(self.digests_path, digest)
        return {"ok": True, "version": APP_VERSION, "digest": digest}

    def digests(self, public: bool = False, *, limit: int = 100) -> list[dict[str, Any]]:
        rows = [row for row in _latest(self.digests_path, "digest_id", self.max_records) if not row.get("deleted")]
        if public:
            rows = [row for row in rows if row.get("status") == "approved" and row.get("published") is True and row.get("visibility") == "public"]
            rows = [{
                "schema": DIGEST_SCHEMA_VERSION,
                "version": APP_VERSION,
                "digest_id": row.get("digest_id"),
                "title": row.get("title"),
                "summary": row.get("summary"),
                "period": row.get("period"),
                "alert_count": row.get("alert_count"),
                "alerts": deepcopy(row.get("alerts") or []),
                "published_at": row.get("published_at") or "",
                "automatic_publication": False,
            } for row in rows]
        return sorted(rows, key=lambda row: str(row.get("created_at") or row.get("published_at") or ""), reverse=True)[:max(1, min(int(limit), 500))]

    def review_digest(self, digest_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        decision = _safe_text(request.get("decision"), 20).lower()
        reviewer = _safe_text(request.get("reviewed_by"), 160)
        reason = _safe_text(request.get("reason"), 1000)
        if decision not in {"approve", "reject"}:
            raise ValueError("decision must be approve or reject.")
        if not reviewer or not reason:
            raise ValueError("reviewed_by and reason are required.")
        target = _safe_id(digest_id, "digest")
        current = next((row for row in self.digests(False, limit=500) if row.get("digest_id") == target), None)
        if current is None:
            raise KeyError(digest_id)
        now = self.now_fn().astimezone(timezone.utc)
        updated = dict(current)
        published = decision == "approve" and current.get("visibility") == "public"
        updated.update({
            "status": "approved" if decision == "approve" else "rejected",
            "reviewed_at": _iso(now),
            "reviewed_by": reviewer,
            "review_reason": reason,
            "published": published,
            "published_at": _iso(now) if published else "",
            "automatic_publication": False,
        })
        updated["digest_sha256"] = _canonical_digest({key: value for key, value in updated.items() if key != "digest_sha256"})
        _append(self.digests_path, updated)
        return {"ok": True, "version": APP_VERSION, "digest": updated}

    def create_handoff(self, digest_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        adapter = _safe_text(request.get("adapter") or "catalyst_communications", 80).lower()
        if adapter not in {"catalyst_communications", "download"}:
            raise ValueError("Unsupported delivery adapter.")
        target = _safe_id(digest_id, "digest")
        digest = next((row for row in self.digests(False, limit=500) if row.get("digest_id") == target), None)
        if digest is None:
            raise KeyError(digest_id)
        if digest.get("status") != "approved":
            raise ValueError("Only human-approved digests may create delivery handoffs.")
        now = self.now_fn().astimezone(timezone.utc)
        handoff = {
            "schema": HANDOFF_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "handoff_id": f"handoff:{uuid4().hex[:20]}",
            "digest_id": target,
            "adapter": adapter,
            "state": "ready_for_external_adapter" if adapter == "catalyst_communications" else "ready_for_download",
            "created_at": _iso(now),
            "payload": {
                "title": digest.get("title"),
                "summary": digest.get("summary"),
                "period": digest.get("period"),
                "alert_count": digest.get("alert_count"),
                "alerts": deepcopy(digest.get("alerts") or []),
                "source_system": "Sustainable Catalyst Site Intelligence",
                "source_version": APP_VERSION,
            },
            "recipient_data_included": False,
            "subscriber_profiles_stored": False,
            "delivery_performed": False,
            "provider_neutral": True,
            "consent_and_unsubscribe_managed_externally": True,
        }
        handoff["handoff_sha256"] = _canonical_digest({key: value for key, value in handoff.items() if key != "handoff_sha256"})
        _append(self.handoffs_path, handoff)
        return {"ok": True, "version": APP_VERSION, "handoff": handoff}

    def public_catalog(self) -> dict[str, Any]:
        rows = self.watchlists(public=True)
        return {
            "ok": True,
            "version": APP_VERSION,
            "schema": WATCHLIST_SCHEMA_VERSION,
            "count": len(rows),
            "watchlists": rows,
            "policy_url": "/public/live-intelligence/subscriptions/policy",
            "preferences_url": "/public/live-intelligence/subscriptions/preferences",
            "subscriber_profiles_stored": False,
        }

    def status(self) -> dict[str, Any]:
        watchlists = self.watchlists(False)
        alerts = self.alerts(False, limit=500)
        digests = self.digests(False, limit=500)
        handoffs = _latest(self.handoffs_path, "handoff_id", self.max_records)
        return {
            "ok": True,
            "version": APP_VERSION,
            "enabled": bool(self.settings.live_intelligence_subscriptions_enabled),
            "watchlist_count": len(watchlists),
            "public_watchlist_count": sum(1 for row in watchlists if row.get("visibility") == "public" and row.get("review_status") == "approved"),
            "pending_alert_count": sum(1 for row in alerts if row.get("status") == "pending_review"),
            "published_alert_count": sum(1 for row in alerts if row.get("published") is True),
            "draft_digest_count": sum(1 for row in digests if row.get("status") == "draft"),
            "handoff_count": len(handoffs),
            "due_watchlist_count": len(self.due_watchlists()),
            "subscriber_profiles_stored": False,
            "automatic_delivery": False,
        }

    def control_center(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": APP_VERSION,
            "policy": subscription_policy(),
            "status": self.status(),
            "watchlists": self.watchlists(False),
            "recent_alerts": self.alerts(False, limit=100),
            "recent_digests": self.digests(False, limit=50),
            "recent_handoffs": sorted(_latest(self.handoffs_path, "handoff_id", self.max_records), key=lambda row: str(row.get("created_at") or ""), reverse=True)[:50],
        }

    def run_due(self, *, dry_run: bool = True, limit: int = 100) -> dict[str, Any]:
        due = self.due_watchlists()[:max(1, min(int(limit), 500))]
        if dry_run:
            return {
                "ok": True,
                "version": APP_VERSION,
                "dry_run": True,
                "due_count": len(due),
                "watchlists": [self._public_watchlist(row) if row.get("visibility") == "public" else {
                    "watchlist_id": row.get("watchlist_id"), "title": row.get("title"), "cadence": row.get("cadence"), "next_due_at": row.get("next_due_at"),
                } for row in due],
            }
        results = []
        for row in due:
            results.append(self.evaluate_watchlist(str(row["watchlist_id"]), {"dry_run": False}))
        return {
            "ok": True,
            "version": APP_VERSION,
            "dry_run": False,
            "due_count": len(due),
            "evaluated_count": len(results),
            "created_alert_count": sum(int(item["evaluation"]["created_alert_count"]) for item in results),
            "results": results,
            "automatic_publication": False,
        }

    def feed_payload(self, watchlist_id: str, format: str = "json") -> tuple[str, str]:
        watchlist = self._watchlist(watchlist_id, public=True)
        alerts = self.alerts(public=True, watchlist_id=watchlist_id, limit=100)
        normalized = _safe_text(format, 12).lower()
        if normalized == "json":
            payload = {
                "ok": True,
                "version": APP_VERSION,
                "schema": ALERT_SCHEMA_VERSION,
                "watchlist": watchlist,
                "alerts": alerts,
                "count": len(alerts),
                "subscriber_profiles_stored": False,
            }
            return "application/json", json.dumps(payload, ensure_ascii=False, sort_keys=True)
        if normalized not in {"rss", "atom"}:
            raise ValueError("format must be json, rss, or atom.")
        base = str(self.settings.site_base_url).rstrip("/")
        feed_url = f"{base}/public/live-intelligence/subscriptions/watchlists/{watchlist_id}/feed?format={normalized}"
        if normalized == "rss":
            items = []
            for alert in alerts:
                signal = alert.get("signal") or {}
                link = _safe_url(signal.get("context_url") or (signal.get("primary_destination") or {}).get("url"))
                items.append(
                    "<item>"
                    f"<guid>{escape(str(alert.get('alert_id') or ''))}</guid>"
                    f"<title>{escape(str(signal.get('label') or 'Live Intelligence signal'))}</title>"
                    f"<description>{escape(str(signal.get('value') or ''))}</description>"
                    f"<link>{escape(base + link if link.startswith('/') else link)}</link>"
                    f"<pubDate>{escape(str(alert.get('published_at') or alert.get('created_at') or ''))}</pubDate>"
                    "</item>"
                )
            body = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><rss version=\"2.0\"><channel>" + f"<title>{escape(watchlist['title'])}</title><link>{escape(feed_url)}</link><description>{escape(watchlist['summary'])}</description>" + "".join(items) + "</channel></rss>"
            return "application/rss+xml", body
        entries = []
        for alert in alerts:
            signal = alert.get("signal") or {}
            link = _safe_url(signal.get("context_url") or (signal.get("primary_destination") or {}).get("url"))
            entries.append(
                "<entry>"
                f"<id>{escape(str(alert.get('alert_id') or ''))}</id>"
                f"<title>{escape(str(signal.get('label') or 'Live Intelligence signal'))}</title>"
                f"<summary>{escape(str(signal.get('value') or ''))}</summary>"
                f"<link href=\"{escape(base + link if link.startswith('/') else link)}\"/>"
                f"<updated>{escape(str(alert.get('published_at') or alert.get('created_at') or ''))}</updated>"
                "</entry>"
            )
        body = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><feed xmlns=\"http://www.w3.org/2005/Atom\">" + f"<id>{escape(feed_url)}</id><title>{escape(watchlist['title'])}</title><updated>{escape(_iso())}</updated>" + "".join(entries) + "</feed>"
        return "application/atom+xml", body
