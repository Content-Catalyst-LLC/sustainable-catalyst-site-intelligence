from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import html
import json
from pathlib import Path
import re
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from .alerts_monitoring_live_streams import build_stream_snapshot, evaluate_alert_rules
from .config import Settings

RELEASE_VERSION = "3.1.4"
SCHEMA_VERSION = "sc-site-intelligence-scheduled-monitoring/1.0"
MONITOR_SCHEMA = "sc-site-intelligence-monitor-definition/1.0"
CHECK_SCHEMA = "sc-site-intelligence-monitor-check/1.0"
ALERT_SCHEMA = "sc-site-intelligence-deduplicated-alert/1.0"
DIGEST_SCHEMA = "sc-site-intelligence-scheduled-digest/1.0"
DELIVERY_SCHEMA = "sc-site-intelligence-delivery-receipt/1.0"
FEED_SCHEMA = "sc-site-intelligence-public-feed/1.0"
CADENCES = {"manual", "hourly", "daily", "weekly"}
DIGEST_PERIODS = {"daily": timedelta(days=1), "weekly": timedelta(days=7)}
VISIBILITY = {"private", "unlisted", "public"}
DIGEST_STATUSES = {"draft", "approved", "published", "archived"}
CHANNELS = {"feed", "email", "webhook"}
_SECRET = re.compile(r"(?:token|secret|password|authorization|api[_-]?key|email|phone|user[_-]?id)", re.I)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else Path(__file__).resolve().parents[2] / path


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _safe_id(value: Any, fallback: str = "record") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.:-]+", "-", str(value or "").strip()).strip("-:.")
    return (cleaned or fallback)[:180]


def _safe_text(value: Any, limit: int = 1000) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value or "")).strip()[:limit]


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): ("[redacted]" if _SECRET.search(str(k)) else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _read_jsonl(path: Path, limit: int = 20000) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except (FileNotFoundError, OSError):
        return []
    rows: list[dict[str, Any]] = []
    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _append(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _latest(path: Path, key: str, limit: int = 20000) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(path, limit):
        if row.get(key):
            latest[str(row[key])] = row
    return list(latest.values())


def _list(value: Any, maximum: int = 100, length: int = 300) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value[:maximum]:
        text = _safe_text(item, length)
        if text and text not in output:
            output.append(text)
    return output


class ScheduledMonitoringCenter:
    def __init__(
        self,
        settings: Settings,
        now_fn: Callable[[], datetime] = _utc_now,
        stream_loader: Callable[..., dict[str, Any]] = build_stream_snapshot,
        delivery_adapters: Mapping[str, Callable[[dict[str, Any]], dict[str, Any]]] | None = None,
    ) -> None:
        self.settings = settings
        self.now_fn = now_fn
        self.stream_loader = stream_loader
        self.adapters = dict(delivery_adapters or {})
        self.monitors_path = _resolve(settings.scheduled_monitoring_monitors_path)
        self.checks_path = _resolve(settings.scheduled_monitoring_checks_path)
        self.alerts_path = _resolve(settings.scheduled_monitoring_alerts_path)
        self.digests_path = _resolve(settings.scheduled_monitoring_digests_path)
        self.deliveries_path = _resolve(settings.scheduled_monitoring_deliveries_path)
        self.feeds_path = _resolve(settings.scheduled_monitoring_feeds_path)
        self.policy = _read_json(_resolve(settings.scheduled_monitoring_policy_path), {})
        self.max_records = settings.scheduled_monitoring_max_records
        self.max_signals = settings.scheduled_monitoring_max_signals
        self.dedupe_hours = settings.scheduled_monitoring_dedupe_hours

    def monitors(self, public: bool = False) -> list[dict[str, Any]]:
        rows = [x for x in _latest(self.monitors_path, "monitor_id", self.max_records) if not x.get("deleted")]
        if public:
            rows = [x for x in rows if x.get("visibility") == "public" and x.get("enabled")]
            return [self._public_monitor(x) for x in rows]
        return sorted(rows, key=lambda x: str(x.get("updated_at", "")), reverse=True)

    def _monitor(self, monitor_id: str) -> dict[str, Any]:
        token = _safe_id(monitor_id)
        for monitor in self.monitors(False):
            if monitor.get("monitor_id") == token:
                return monitor
        raise KeyError(token)

    def _public_monitor(self, monitor: dict[str, Any]) -> dict[str, Any]:
        return {
            "monitor_id": monitor.get("monitor_id"), "title": monitor.get("title"),
            "summary": monitor.get("summary"), "cadence": monitor.get("cadence"),
            "families": monitor.get("families", []), "countries": monitor.get("countries", []),
            "visibility": monitor.get("visibility"), "feed_id": monitor.get("feed_id", ""),
            "last_checked_at": monitor.get("last_checked_at", ""), "next_due_at": monitor.get("next_due_at", ""),
            "methodology": "Matches are deterministic evaluations of public source records; absence of a match is not proof that no real-world change occurred.",
        }

    def save_monitor(self, request: dict[str, Any]) -> dict[str, Any]:
        title = _safe_text(request.get("title"), 300)
        if not title:
            raise ValueError("title is required.")
        monitor_id = _safe_id(request.get("monitor_id") or f"monitor:{uuid4().hex[:16]}")
        previous = next((x for x in self.monitors(False) if x.get("monitor_id") == monitor_id), None)
        cadence = _safe_text(request.get("cadence") or (previous or {}).get("cadence") or "daily", 20).lower()
        visibility = _safe_text(request.get("visibility") or (previous or {}).get("visibility") or "private", 20).lower()
        if cadence not in CADENCES or visibility not in VISIBILITY:
            raise ValueError("Unsupported cadence or visibility.")
        rules = request.get("rules") if isinstance(request.get("rules"), list) else (previous or {}).get("rules", [])
        if len(rules) > 50:
            raise ValueError("A monitor may contain at most 50 rules.")
        channels = [x for x in _list(request.get("channels") or (previous or {}).get("channels", ["feed"]), 3, 20) if x in CHANNELS]
        quiet = request.get("quiet_hours_utc") if isinstance(request.get("quiet_hours_utc"), dict) else (previous or {}).get("quiet_hours_utc", {})
        now = self.now_fn()
        record = {
            "schema": MONITOR_SCHEMA, "release_version": RELEASE_VERSION, "monitor_id": monitor_id,
            "title": title, "summary": _safe_text(request.get("summary") or (previous or {}).get("summary"), 3000),
            "enabled": bool(request.get("enabled", (previous or {}).get("enabled", True))), "cadence": cadence,
            "visibility": visibility, "families": _list(request.get("families") or (previous or {}).get("families", []), 12, 40),
            "countries": [x.upper() for x in _list(request.get("countries") or (previous or {}).get("countries", []), 100, 20)],
            "query": _safe_text(request.get("query") or (previous or {}).get("query"), 240),
            "source_id": _safe_text(request.get("source_id") or (previous or {}).get("source_id"), 180),
            "freshness": _safe_text(request.get("freshness") or (previous or {}).get("freshness"), 80),
            "rules": _redact(rules), "channels": channels or ["feed"],
            "digest_period": _safe_text(request.get("digest_period") or (previous or {}).get("digest_period") or "daily", 20),
            "quiet_hours_utc": {"start": int(quiet.get("start", 22)) % 24, "end": int(quiet.get("end", 7)) % 24},
            "max_notifications_per_day": max(1, min(int(request.get("max_notifications_per_day", (previous or {}).get("max_notifications_per_day", 20))), 500)),
            "feed_id": _safe_id(request.get("feed_id") or (previous or {}).get("feed_id") or f"feed:{monitor_id}"),
            "created_at": (previous or {}).get("created_at") or _iso(now), "updated_at": _iso(now),
            "last_checked_at": (previous or {}).get("last_checked_at", ""), "next_due_at": (previous or {}).get("next_due_at", _iso(now)),
            "automatic_publication": False, "individual_tracking": False, "emergency_dispatch": False,
        }
        record["monitor_sha256"] = _digest({k: v for k, v in record.items() if k != "monitor_sha256"})
        _append(self.monitors_path, record)
        return {"ok": True, "monitor": record}

    def _cadence_delta(self, cadence: str) -> timedelta | None:
        return {"hourly": timedelta(hours=1), "daily": timedelta(days=1), "weekly": timedelta(days=7)}.get(cadence)

    def due_monitors(self, at: datetime | None = None) -> list[dict[str, Any]]:
        now = at or self.now_fn()
        due = []
        for monitor in self.monitors(False):
            if not monitor.get("enabled") or monitor.get("cadence") == "manual":
                continue
            due_at = _parse(monitor.get("next_due_at"))
            if due_at is None or due_at <= now:
                due.append(monitor)
        return due

    def _recent_fingerprints(self, since: datetime) -> set[str]:
        return {
            str(x.get("fingerprint")) for x in _read_jsonl(self.alerts_path, self.max_records)
            if x.get("fingerprint") and (_parse(x.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)) >= since
        }

    def check_monitor(self, monitor_id: str, request: dict[str, Any] | None = None) -> dict[str, Any]:
        request = request or {}
        monitor = self._monitor(monitor_id)
        now = self.now_fn()
        provided = request.get("signals") if isinstance(request.get("signals"), list) else None
        if provided is None:
            snapshot = self.stream_loader(
                self.settings, families=monitor.get("families") or None,
                country=(monitor.get("countries") or [""])[0], query=monitor.get("query", ""),
                source_id=monitor.get("source_id", ""), freshness=monitor.get("freshness", ""),
                limit=self.max_signals,
            )
            signals = snapshot.get("signals", [])
            source_state = snapshot.get("state", "unknown")
        else:
            signals = [dict(x) for x in provided if isinstance(x, Mapping)][:self.max_signals]
            source_state = "provided"
        evaluation = evaluate_alert_rules(self.settings, rules=monitor.get("rules", []), signals=signals)
        known = self._recent_fingerprints(now - timedelta(hours=self.dedupe_hours))
        created: list[dict[str, Any]] = []
        duplicates = 0
        for match in evaluation.get("matches", []):
            rule = match.get("rule") or {}
            signal = match.get("signal") or {}
            seed = {
                "monitor_id": monitor["monitor_id"], "rule_id": rule.get("id"), "signal_id": signal.get("signal_id") or signal.get("id"),
                "observed_at": signal.get("observed_at"), "value_number": signal.get("value_number"), "source_id": signal.get("source_id"),
            }
            fingerprint = _digest(seed)
            if fingerprint in known:
                duplicates += 1
                continue
            alert = {
                "schema": ALERT_SCHEMA, "release_version": RELEASE_VERSION,
                "alert_id": f"alert:{uuid4().hex[:16]}", "monitor_id": monitor["monitor_id"],
                "rule_id": rule.get("id", ""), "rule_name": rule.get("name", ""),
                "signal": _redact(signal), "fingerprint": fingerprint,
                "group_key": ":".join([_safe_text(signal.get("family"), 40), _safe_text(signal.get("source_id"), 100), ",".join(signal.get("countries") or [])]),
                "created_at": _iso(now), "acknowledged": False,
                "operational_emergency_alert": False, "automated_consequential_action": False,
            }
            alert["alert_sha256"] = _digest({k: v for k, v in alert.items() if k != "alert_sha256"})
            _append(self.alerts_path, alert)
            known.add(fingerprint)
            created.append(alert)
        next_due = now + (self._cadence_delta(str(monitor.get("cadence"))) or timedelta(days=3650))
        monitor_update = dict(monitor)
        monitor_update.update({"last_checked_at": _iso(now), "next_due_at": _iso(next_due), "updated_at": _iso(now)})
        monitor_update["monitor_sha256"] = _digest({k: v for k, v in monitor_update.items() if k != "monitor_sha256"})
        _append(self.monitors_path, monitor_update)
        receipt = {
            "schema": CHECK_SCHEMA, "release_version": RELEASE_VERSION, "check_id": f"check:{uuid4().hex[:16]}",
            "monitor_id": monitor["monitor_id"], "started_at": _iso(now), "completed_at": _iso(self.now_fn()),
            "source_state": source_state, "signal_count": len(signals), "match_count": evaluation.get("match_count", 0),
            "new_alert_count": len(created), "duplicate_count": duplicates, "next_due_at": _iso(next_due),
            "status": "completed", "notification_sent": False,
        }
        receipt["check_sha256"] = _digest({k: v for k, v in receipt.items() if k != "check_sha256"})
        _append(self.checks_path, receipt)
        return {"ok": True, "receipt": receipt, "new_alerts": created, "duplicates_suppressed": duplicates}

    def run_due(self, dry_run: bool = True, limit: int = 100) -> dict[str, Any]:
        due = self.due_monitors()[:max(1, min(limit, 500))]
        if dry_run:
            return {"ok": True, "dry_run": True, "due_count": len(due), "monitors": [self._public_monitor(x) for x in due], "persistent_scheduler_active": False}
        results = []
        for monitor in due:
            try:
                results.append(self.check_monitor(str(monitor["monitor_id"])))
            except Exception as exc:
                results.append({"ok": False, "monitor_id": monitor.get("monitor_id"), "error": _safe_text(exc, 500)})
        return {"ok": True, "dry_run": False, "due_count": len(due), "results": results, "persistent_scheduler_active": False}

    def alerts(self, monitor_ids: Sequence[str] | None = None, since: datetime | None = None, public: bool = False) -> list[dict[str, Any]]:
        wanted = {_safe_id(x) for x in (monitor_ids or [])}
        public_ids = {x["monitor_id"] for x in self.monitors(True)} if public else set()
        rows = []
        for row in _read_jsonl(self.alerts_path, self.max_records):
            if wanted and row.get("monitor_id") not in wanted:
                continue
            if public and row.get("monitor_id") not in public_ids:
                continue
            created = _parse(row.get("created_at"))
            if since and (created is None or created < since):
                continue
            rows.append(row)
        rows.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return rows

    def generate_digest(self, request: dict[str, Any]) -> dict[str, Any]:
        period = _safe_text(request.get("period") or "daily", 20).lower()
        if period not in DIGEST_PERIODS:
            raise ValueError("period must be daily or weekly.")
        now = self.now_fn()
        monitor_ids = _list(request.get("monitor_ids"), 200, 180)
        rows = self.alerts(monitor_ids, now - DIGEST_PERIODS[period], public=False)
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for alert in rows:
            groups[str(alert.get("group_key") or "ungrouped")].append(alert)
        digest_id = _safe_id(request.get("digest_id") or f"digest:{period}:{now.strftime('%Y%m%d%H%M%S')}:{uuid4().hex[:6]}")
        visibility = _safe_text(request.get("visibility") or "private", 20).lower()
        if visibility not in VISIBILITY:
            raise ValueError("Unsupported digest visibility.")
        record = {
            "schema": DIGEST_SCHEMA, "release_version": RELEASE_VERSION, "digest_id": digest_id,
            "title": _safe_text(request.get("title") or f"{period.title()} public intelligence digest", 500),
            "summary": _safe_text(request.get("summary") or f"Deterministic digest of {len(rows)} deduplicated monitor alerts.", 3000),
            "period": period, "window_start": _iso(now - DIGEST_PERIODS[period]), "window_end": _iso(now),
            "monitor_ids": monitor_ids, "visibility": visibility, "status": "draft",
            "alert_count": len(rows), "group_count": len(groups),
            "groups": [{"group_key": key, "count": len(items), "alerts": items[:50]} for key, items in sorted(groups.items())],
            "family_counts": dict(Counter((a.get("signal") or {}).get("family", "unknown") for a in rows)),
            "source_counts": dict(Counter((a.get("signal") or {}).get("source_id", "unknown") for a in rows)),
            "created_at": _iso(now), "updated_at": _iso(now), "approved_at": "", "published_at": "",
            "ai_generated": False, "automatic_publication": False, "emergency_instruction": False,
        }
        record["digest_sha256"] = _digest({k: v for k, v in record.items() if k != "digest_sha256"})
        _append(self.digests_path, record)
        return {"ok": True, "digest": record}

    def digests(self, public: bool = False, limit: int = 100) -> list[dict[str, Any]]:
        rows = [x for x in _latest(self.digests_path, "digest_id", self.max_records) if not x.get("deleted")]
        if public:
            rows = [x for x in rows if x.get("status") == "published" and x.get("visibility") in {"public", "unlisted"}]
        rows.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return rows[:max(1, min(limit, 1000))]

    def approve_digest(self, digest_id: str, request: dict[str, Any]) -> dict[str, Any]:
        row = next((x for x in self.digests(False, 1000) if x.get("digest_id") == _safe_id(digest_id)), None)
        if not row:
            raise KeyError(digest_id)
        if not bool(request.get("human_confirmed")):
            raise ValueError("human_confirmed=true is required.")
        action = _safe_text(request.get("action") or "approve", 20).lower()
        if action not in {"approve", "publish"}:
            raise ValueError("action must be approve or publish.")
        now = self.now_fn()
        updated = dict(row)
        updated["status"] = "published" if action == "publish" else "approved"
        updated["approved_at"] = updated.get("approved_at") or _iso(now)
        if action == "publish":
            updated["published_at"] = _iso(now)
        updated["reviewer"] = _safe_text(request.get("reviewer") or "human-reviewer", 200)
        updated["updated_at"] = _iso(now)
        updated["digest_sha256"] = _digest({k: v for k, v in updated.items() if k != "digest_sha256"})
        _append(self.digests_path, updated)
        return {"ok": True, "digest": updated}

    def save_feed(self, request: dict[str, Any]) -> dict[str, Any]:
        title = _safe_text(request.get("title"), 300)
        if not title:
            raise ValueError("title is required.")
        feed_id = _safe_id(request.get("feed_id") or f"feed:{uuid4().hex[:16]}")
        visibility = _safe_text(request.get("visibility") or "public", 20).lower()
        if visibility not in {"public", "unlisted"}:
            raise ValueError("Public feeds must be public or unlisted.")
        now = self.now_fn()
        record = {
            "schema": FEED_SCHEMA, "release_version": RELEASE_VERSION, "feed_id": feed_id,
            "title": title, "description": _safe_text(request.get("description"), 2000),
            "monitor_ids": _list(request.get("monitor_ids"), 200, 180), "visibility": visibility,
            "enabled": bool(request.get("enabled", True)), "created_at": _iso(now), "updated_at": _iso(now),
            "hosted_profile_required": False, "subscriber_tracking": False,
        }
        record["feed_sha256"] = _digest({k: v for k, v in record.items() if k != "feed_sha256"})
        _append(self.feeds_path, record)
        return {"ok": True, "feed": record}

    def feeds(self, public: bool = True) -> list[dict[str, Any]]:
        rows = [x for x in _latest(self.feeds_path, "feed_id", self.max_records) if x.get("enabled") and not x.get("deleted")]
        if public:
            rows = [x for x in rows if x.get("visibility") == "public"]
        return sorted(rows, key=lambda x: str(x.get("title", "")))

    def feed_payload(self, feed_id: str, format_name: str = "json") -> tuple[str, str]:
        feed = next((x for x in self.feeds(False) if x.get("feed_id") == _safe_id(feed_id)), None)
        if not feed:
            raise KeyError(feed_id)
        digests = [x for x in self.digests(True, 100) if not feed.get("monitor_ids") or set(x.get("monitor_ids", [])) & set(feed.get("monitor_ids", []))]
        payload = {"ok": True, "schema": FEED_SCHEMA, "version": RELEASE_VERSION, "feed": feed, "items": digests, "count": len(digests), "subscriber_tracking": False}
        if format_name == "json":
            return "application/json", json.dumps(payload, ensure_ascii=False, sort_keys=True)
        base = self.settings.site_base_url.rstrip("/")
        items = []
        for digest in digests[:50]:
            link = f"{base}/?scsi_digest={html.escape(str(digest.get('digest_id', '')))}"
            if format_name == "rss":
                items.append(f"<item><title>{html.escape(str(digest.get('title','')))}</title><link>{link}</link><guid>{html.escape(str(digest.get('digest_sha256','')))}</guid><pubDate>{html.escape(str(digest.get('published_at') or digest.get('created_at','')))}</pubDate><description>{html.escape(str(digest.get('summary','')))}</description></item>")
            else:
                items.append(f"<entry><id>{html.escape(str(digest.get('digest_sha256','')))}</id><title>{html.escape(str(digest.get('title','')))}</title><updated>{html.escape(str(digest.get('published_at') or digest.get('created_at','')))}</updated><link href=\"{link}\"/><summary>{html.escape(str(digest.get('summary','')))}</summary></entry>")
        if format_name == "rss":
            xml = f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{html.escape(str(feed.get("title","")))}</title><link>{base}</link><description>{html.escape(str(feed.get("description","")))}</description>{"".join(items)}</channel></rss>'
            return "application/rss+xml", xml
        if format_name == "atom":
            xml = f'<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom"><id>{html.escape(str(feed.get("feed_sha256","")))}</id><title>{html.escape(str(feed.get("title","")))}</title><updated>{_iso(self.now_fn())}</updated>{"".join(items)}</feed>'
            return "application/atom+xml", xml
        raise ValueError("format must be json, rss, or atom.")

    def _quiet(self, monitor: dict[str, Any], now: datetime) -> bool:
        quiet = monitor.get("quiet_hours_utc") or {}
        start, end = int(quiet.get("start", 22)), int(quiet.get("end", 7))
        hour = now.hour
        return start <= hour < end if start < end else hour >= start or hour < end

    def deliver_digest(self, digest_id: str, request: dict[str, Any]) -> dict[str, Any]:
        digest = next((x for x in self.digests(False, 1000) if x.get("digest_id") == _safe_id(digest_id)), None)
        if not digest:
            raise KeyError(digest_id)
        if digest.get("status") != "published":
            raise ValueError("Only human-approved published digests may be delivered.")
        channel = _safe_text(request.get("channel") or "feed", 20).lower()
        if channel not in CHANNELS:
            raise ValueError("Unsupported delivery channel.")
        now = self.now_fn()
        monitor_ids = digest.get("monitor_ids") or []
        monitors = [self._monitor(x) for x in monitor_ids if any(m.get("monitor_id") == _safe_id(x) for m in self.monitors(False))]
        if any(self._quiet(m, now) for m in monitors) and channel != "feed" and not request.get("override_quiet_hours"):
            state, detail = "deferred", "Delivery is inside a configured UTC quiet period."
        elif channel == "feed":
            state, detail = "published", "Digest is available through configured public feeds."
        elif channel == "email" and not self.settings.scheduled_monitoring_email_enabled:
            state, detail = "skipped", "Email delivery adapter is disabled."
        elif channel == "webhook" and not self.settings.scheduled_monitoring_webhook_enabled:
            state, detail = "skipped", "Webhook delivery adapter is disabled."
        elif channel not in self.adapters:
            state, detail = "queued", "Adapter is enabled but no runtime delivery implementation is attached."
        else:
            result = self.adapters[channel]({"digest": digest, "request": _redact(request)})
            state, detail = _safe_text(result.get("state") or "delivered", 40), _safe_text(result.get("detail"), 500)
        receipt = {
            "schema": DELIVERY_SCHEMA, "release_version": RELEASE_VERSION, "delivery_id": f"delivery:{uuid4().hex[:16]}",
            "digest_id": digest["digest_id"], "channel": channel, "state": state, "detail": detail,
            "created_at": _iso(now), "recipient_or_url": "[redacted]" if channel in {"email", "webhook"} else "public-feed",
            "conversation_data_shared": False, "automatic_emergency_notification": False,
        }
        receipt["delivery_sha256"] = _digest({k: v for k, v in receipt.items() if k != "delivery_sha256"})
        _append(self.deliveries_path, receipt)
        return {"ok": True, "delivery": receipt}

    def public_summary(self) -> dict[str, Any]:
        monitors = self.monitors(True)
        feeds = self.feeds(True)
        digests = [x for x in self.digests(True, 50) if x.get("visibility") == "public"]
        return {
            "ok": True, "schema": SCHEMA_VERSION, "version": RELEASE_VERSION,
            "release_name": "Scheduled Monitoring, Digests, and Public Intelligence Feeds",
            "generated_at": _iso(self.now_fn()), "monitor_count": len(monitors), "feed_count": len(feeds),
            "published_digest_count": len(digests), "monitors": monitors, "feeds": feeds, "latest_digests": digests[:20],
            "formats": ["json", "rss", "atom"], "hosted_profile_required": False,
            "governance": {"emergency_service": False, "individual_tracking": False, "automatic_publication": False, "hidden_risk_score": False},
        }

    def diagnostics(self, public: bool = True) -> dict[str, Any]:
        monitors = self.monitors(False)
        checks = _read_jsonl(self.checks_path, self.max_records)
        alerts = _read_jsonl(self.alerts_path, self.max_records)
        deliveries = _read_jsonl(self.deliveries_path, self.max_records)
        payload = {
            "ok": True, "version": RELEASE_VERSION, "enabled": self.settings.scheduled_monitoring_enabled,
            "monitor_count": len(monitors), "enabled_monitor_count": sum(1 for x in monitors if x.get("enabled")),
            "due_monitor_count": len(self.due_monitors()), "check_count": len(checks), "alert_count": len(alerts),
            "digest_count": len(self.digests(False, 10000)), "delivery_count": len(deliveries), "feed_count": len(self.feeds(False)),
            "dedupe_hours": self.dedupe_hours, "persistent_scheduler_active": False,
            "email_adapter_enabled": self.settings.scheduled_monitoring_email_enabled,
            "webhook_adapter_enabled": self.settings.scheduled_monitoring_webhook_enabled,
            "writable_state_paths": [] if public else [str(self.monitors_path), str(self.checks_path), str(self.alerts_path), str(self.digests_path), str(self.deliveries_path), str(self.feeds_path)],
            "policy": self.policy,
        }
        return payload

    def control_center(self) -> dict[str, Any]:
        return {
            "ok": True, "version": RELEASE_VERSION, "summary": self.diagnostics(public=False),
            "monitors": self.monitors(False), "due_monitors": self.due_monitors(),
            "recent_checks": _read_jsonl(self.checks_path, 100)[-100:][::-1],
            "recent_alerts": self.alerts(None, None, False)[:100], "digests": self.digests(False, 100),
            "deliveries": _read_jsonl(self.deliveries_path, 100)[-100:][::-1], "feeds": self.feeds(False),
            "scheduler_note": "No always-on scheduler is claimed. Invoke the due-job endpoint from an explicit hourly or lower-frequency scheduler.",
        }
