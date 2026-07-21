"""Source-bound Live Intelligence briefings and publication handoffs.

Site Intelligence v3.14.0 converts canonical signals, reviewed alerts, and
approved digests into editorial briefing drafts. The system assembles evidence,
chronology, and source-linked claims, but it does not publish interpretation or
write to WordPress automatically. Public release always requires a documented
human review decision.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from .config import Settings
from .version import APP_VERSION

POLICY_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-briefing-policy/1.0"
BRIEFING_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-briefing/1.0"
CLAIM_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-briefing-claim/1.0"
PACKAGE_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-publication-package/1.0"
HANDOFF_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-publication-handoff/1.0"

ALLOWED_BRIEFING_TYPES = ("signal", "alert", "digest", "channel", "regional")
ALLOWED_VISIBILITY = ("private", "public")
ALLOWED_HANDOFF_ADAPTERS = ("knowledge_library", "publications", "decision_studio", "download")
DENIED_IDENTITY_FIELDS = {
    "subscriber", "subscriber_id", "subscriber_email", "email", "email_address",
    "phone", "phone_number", "user_id", "account_id", "session_id", "cookie",
    "ip", "ip_address", "user_agent", "referrer", "recipient", "recipients",
    "mailing_list", "contact_id", "profile", "personalization", "metadata",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None = None) -> str:
    return (value or _utc_now()).astimezone(timezone.utc).isoformat()


def _safe_text(value: Any, limit: int = 500) -> str:
    return " ".join(str(value or "").split())[:limit]


def _safe_id(value: Any, prefix: str = "item") -> str:
    text = _safe_text(value, 180).lower()
    text = re.sub(r"[^a-z0-9._:-]+", "-", text).strip("-._:")
    return text or f"{prefix}:{uuid4().hex[:16]}"


def _safe_url(value: Any) -> str:
    text = str(value or "").strip()
    return text[:1200] if text.startswith(("https://", "http://", "/")) else ""


def _resolve(value: str) -> Path:
    return Path(value).expanduser()


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _append(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(record), sort_keys=True, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except (FileNotFoundError, OSError):
        return []
    rows: list[dict[str, Any]] = []
    for line in lines:
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _latest(path: Path, key: str, limit: int) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(path, limit):
        row_id = _safe_text(row.get(key), 180)
        if row_id:
            rows[row_id] = row
    return list(rows.values())


def _reject_identity_payload(value: Any, path: str = "request") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in DENIED_IDENTITY_FIELDS:
                raise ValueError(
                    f"{path}.{key} is not accepted; recipient identities and subscriber profiles are outside Site Intelligence."
                )
            _reject_identity_payload(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_identity_payload(child, f"{path}[{index}]")


def _list(value: Any, maximum: int = 100, item_limit: int = 180) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    output: list[str] = []
    for item in value[:maximum]:
        text = _safe_text(item, item_limit)
        if text and text not in output:
            output.append(text)
    return output


def _source_time(source: Mapping[str, Any]) -> str:
    for key in ("observed_at", "published_at", "updated_at", "created_at"):
        value = _safe_text(source.get(key), 80)
        if value:
            return value
    return ""


def _source_snapshot(source: Mapping[str, Any], source_type: str) -> dict[str, Any]:
    signal = source.get("signal") if isinstance(source.get("signal"), Mapping) else source
    primary = signal.get("primary_destination") if isinstance(signal.get("primary_destination"), Mapping) else {}
    source_id = _safe_text(
        source.get("alert_id") or source.get("digest_id") or signal.get("signal_id") or signal.get("event_id"), 180
    )
    label = _safe_text(
        source.get("title") or source.get("watchlist_title") or signal.get("label") or signal.get("short_label"), 260
    )
    value = _safe_text(signal.get("formatted_value") or signal.get("value") or source.get("summary"), 500)
    return {
        "source_ref": f"{source_type}:{source_id or uuid4().hex[:12]}",
        "source_type": source_type,
        "source_id": source_id,
        "label": label or source_type.title(),
        "value": value,
        "summary": _safe_text(source.get("summary") or source.get("interpretation") or signal.get("detail"), 1600),
        "source_name": _safe_text(signal.get("source_name") or signal.get("source_label"), 220),
        "source_url": _safe_url(signal.get("source_url")),
        "context_url": _safe_url(signal.get("context_url") or primary.get("url")),
        "freshness_state": _safe_text(signal.get("freshness_state"), 60),
        "signal_family": _safe_text(signal.get("signal_family"), 100),
        "geography": deepcopy(signal.get("geography") or {}),
        "observed_at": _source_time(signal) or _source_time(source),
        "reviewed": bool(source.get("status") == "approved" or source.get("published") is True),
    }


def briefing_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "principle": "Assemble source-linked editorial drafts while keeping interpretation and publication under human control.",
        "briefing_types": list(ALLOWED_BRIEFING_TYPES),
        "handoff_adapters": list(ALLOWED_HANDOFF_ADAPTERS),
        "routes": {
            "briefings": "/public/live-intelligence/briefings",
            "templates": "/public/live-intelligence/briefings/templates",
            "policy": "/public/live-intelligence/briefings/policy",
        },
        "boundaries": {
            "automatic_publication": False,
            "automatic_wordpress_write": False,
            "autonomous_interpretation": False,
            "fabricated_sources": False,
            "unsupported_claims_allowed": False,
            "human_review_required": True,
            "source_links_required": True,
            "recipient_identities_stored": False,
            "provider_neutral_handoffs": True,
        },
    }


def briefing_templates() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": POLICY_SCHEMA_VERSION,
        "templates": [
            {"type": "signal", "label": "Signal briefing", "purpose": "Explain one or more canonical observations."},
            {"type": "alert", "label": "Reviewed alert briefing", "purpose": "Contextualize human-reviewed watchlist matches."},
            {"type": "digest", "label": "Digest briefing", "purpose": "Turn an approved alert digest into a source-linked narrative draft."},
            {"type": "channel", "label": "Channel briefing", "purpose": "Summarize a governed thematic signal surface."},
            {"type": "regional", "label": "Regional briefing", "purpose": "Organize geographically bounded observations without causal inference."},
        ],
        "required_sections": ["executive_summary", "key_observations", "evidence", "chronology", "limitations", "sources"],
        "automatic_publication": False,
    }


class LiveIntelligenceBriefingCenter:
    def __init__(
        self,
        settings: Settings,
        *,
        source_loader: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        subscription_center: Any | None = None,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.settings = settings
        self.source_loader = source_loader
        self.subscription_center = subscription_center
        self.now_fn = now_fn
        self.briefings_path = _resolve(settings.live_intelligence_briefings_path)
        self.packages_path = _resolve(settings.live_intelligence_briefing_packages_path)
        self.handoffs_path = _resolve(settings.live_intelligence_briefing_handoffs_path)
        self.max_records = int(settings.live_intelligence_briefings_max_records)
        self.max_sources = int(settings.live_intelligence_briefings_max_sources)

    def _sources(self, request: Mapping[str, Any]) -> list[dict[str, Any]]:
        sources: list[dict[str, Any]] = []
        supplied = request.get("signals") if isinstance(request.get("signals"), list) else []
        for row in supplied:
            if isinstance(row, Mapping):
                sources.append(_source_snapshot(row, "signal"))

        if self.source_loader is not None:
            loaded = self.source_loader(request)
            for row in loaded.get("signals", []) if isinstance(loaded, Mapping) else []:
                if isinstance(row, Mapping):
                    sources.append(_source_snapshot(row, "signal"))

        if self.subscription_center is not None:
            alert_ids = set(_list(request.get("alert_ids"), maximum=self.max_sources))
            digest_ids = set(_list(request.get("digest_ids"), maximum=self.max_sources))
            if alert_ids:
                for row in self.subscription_center.alerts(False, limit=1000):
                    if row.get("alert_id") in alert_ids and row.get("status") == "approved":
                        sources.append(_source_snapshot(row, "alert"))
            if digest_ids:
                for row in self.subscription_center.digests(False, limit=500):
                    if row.get("digest_id") in digest_ids and row.get("status") == "approved":
                        sources.append(_source_snapshot(row, "digest"))

        unique: dict[str, dict[str, Any]] = {}
        for source in sources:
            key = str(source.get("source_ref") or "")
            if key and key not in unique:
                unique[key] = source
        return list(unique.values())[: self.max_sources]

    def _claims(self, sources: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        claims: list[dict[str, Any]] = []
        for index, source in enumerate(sources, start=1):
            label = _safe_text(source.get("label"), 260)
            value = _safe_text(source.get("value"), 500)
            observed = _safe_text(source.get("observed_at"), 80)
            source_name = _safe_text(source.get("source_name"), 220)
            text = label
            if value:
                text += f": {value}"
            if observed:
                text += f" (observed or published {observed})"
            claim = {
                "schema": CLAIM_SCHEMA_VERSION,
                "claim_id": f"claim:{index}",
                "claim_type": "source_bound_observation",
                "text": text,
                "source_refs": [source.get("source_ref")],
                "source_name": source_name,
                "source_url": source.get("source_url") or "",
                "context_url": source.get("context_url") or "",
                "human_verified": False,
                "causal_inference": False,
                "prediction": False,
            }
            claims.append(claim)
        return claims

    def create_draft(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        title = _safe_text(request.get("title"), 280)
        if not title:
            raise ValueError("title is required.")
        briefing_type = _safe_text(request.get("briefing_type") or "signal", 40).lower()
        visibility = _safe_text(request.get("visibility") or "private", 20).lower()
        if briefing_type not in ALLOWED_BRIEFING_TYPES:
            raise ValueError("Unsupported briefing_type.")
        if visibility not in ALLOWED_VISIBILITY:
            raise ValueError("visibility must be private or public.")
        sources = self._sources(request)
        if not sources:
            raise ValueError("At least one canonical signal, reviewed alert, or approved digest is required.")
        claims = self._claims(sources)
        chronology = sorted(
            [
                {"source_ref": source.get("source_ref"), "label": source.get("label"), "time": source.get("observed_at")}
                for source in sources if source.get("observed_at")
            ],
            key=lambda row: str(row.get("time") or ""),
        )
        summary = _safe_text(request.get("executive_summary"), 3000)
        if not summary:
            summary = (
                f"Editorial draft based on {len(sources)} source-linked Live Intelligence item"
                f"{'s' if len(sources) != 1 else ''}. It organizes observations for review and does not assert causation."
            )
        now = self.now_fn().astimezone(timezone.utc)
        record = {
            "schema": BRIEFING_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "briefing_id": _safe_id(request.get("briefing_id") or f"briefing:{uuid4().hex[:20]}", "briefing"),
            "briefing_type": briefing_type,
            "title": title,
            "deck": _safe_text(request.get("deck"), 600),
            "visibility": visibility,
            "status": "draft",
            "executive_summary": summary,
            "key_observations": [claim["text"] for claim in claims],
            "claims": claims,
            "evidence": deepcopy(sources),
            "chronology": chronology,
            "limitations": [
                "This draft contains source-bound observations, not autonomous interpretation.",
                "Absence from the briefing does not establish absence in the underlying world.",
                "Freshness, geographic scope, and source methodology must be reviewed before publication.",
            ],
            "source_count": len(sources),
            "claim_count": len(claims),
            "created_at": _iso(now),
            "updated_at": _iso(now),
            "reviewed_at": "",
            "reviewed_by": "",
            "review_reason": "",
            "published": False,
            "published_at": "",
            "automatic_publication": False,
            "automatic_wordpress_write": False,
            "narrative_method": "deterministic_source_bound_template",
            "human_review_required": True,
        }
        record["briefing_sha256"] = _digest({key: value for key, value in record.items() if key != "briefing_sha256"})
        _append(self.briefings_path, record)
        return {"ok": True, "version": APP_VERSION, "briefing": record}

    def briefings(self, public: bool = False, limit: int = 100) -> list[dict[str, Any]]:
        rows = [row for row in _latest(self.briefings_path, "briefing_id", self.max_records) if not row.get("deleted")]
        if public:
            rows = [
                self._public_briefing(row) for row in rows
                if row.get("visibility") == "public" and row.get("status") == "approved" and row.get("published") is True
            ]
        return sorted(rows, key=lambda row: str(row.get("published_at") or row.get("created_at") or ""), reverse=True)[:max(1, min(int(limit), 500))]

    def _briefing(self, briefing_id: str, public: bool = False) -> dict[str, Any]:
        target = _safe_id(briefing_id, "briefing")
        for row in self.briefings(public=public, limit=500):
            if row.get("briefing_id") == target:
                return row
        raise KeyError(target)

    def _public_briefing(self, row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "schema": BRIEFING_SCHEMA_VERSION,
            "version": APP_VERSION,
            "briefing_id": row.get("briefing_id"),
            "briefing_type": row.get("briefing_type"),
            "title": row.get("title"),
            "deck": row.get("deck"),
            "executive_summary": row.get("executive_summary"),
            "key_observations": deepcopy(row.get("key_observations") or []),
            "claims": deepcopy(row.get("claims") or []),
            "evidence": deepcopy(row.get("evidence") or []),
            "chronology": deepcopy(row.get("chronology") or []),
            "limitations": deepcopy(row.get("limitations") or []),
            "source_count": row.get("source_count", 0),
            "published_at": row.get("published_at") or "",
            "automatic_publication": False,
            "human_reviewed": True,
            "export_urls": {
                "json": f"/public/live-intelligence/briefings/{row.get('briefing_id')}/export?format=json",
                "markdown": f"/public/live-intelligence/briefings/{row.get('briefing_id')}/export?format=markdown",
            },
        }

    def review_briefing(self, briefing_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        decision = _safe_text(request.get("decision"), 20).lower()
        reviewer = _safe_text(request.get("reviewed_by"), 160)
        reason = _safe_text(request.get("reason"), 1200)
        if decision not in {"approve", "reject"}:
            raise ValueError("decision must be approve or reject.")
        if not reviewer or not reason:
            raise ValueError("reviewed_by and reason are required.")
        current = self._briefing(briefing_id, public=False)
        claims = current.get("claims") if isinstance(current.get("claims"), list) else []
        if decision == "approve" and any(not claim.get("source_refs") for claim in claims if isinstance(claim, Mapping)):
            raise ValueError("Every approved claim must retain at least one source reference.")
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
            "updated_at": _iso(now),
            "automatic_publication": False,
        })
        updated["claims"] = [dict(claim, human_verified=(decision == "approve")) for claim in claims if isinstance(claim, Mapping)]
        updated["briefing_sha256"] = _digest({key: value for key, value in updated.items() if key != "briefing_sha256"})
        _append(self.briefings_path, updated)
        return {"ok": True, "version": APP_VERSION, "briefing": updated}

    def package_payload(self, briefing_id: str, format: str = "json", *, public: bool = False) -> tuple[str, str]:
        briefing = self._briefing(briefing_id, public=public)
        if briefing.get("status") != "approved" and not public:
            raise ValueError("Only human-approved briefings may create publication packages.")
        public_row = briefing if public else self._public_briefing(briefing)
        package = {
            "schema": PACKAGE_SCHEMA_VERSION,
            "version": APP_VERSION,
            "briefing": public_row,
            "publication_performed": False,
            "wordpress_write_performed": False,
            "generated_at": _iso(self.now_fn()),
        }
        if format == "json":
            return "application/json", json.dumps(package, indent=2, ensure_ascii=False)
        if format != "markdown":
            raise ValueError("format must be json or markdown.")
        lines = [f"# {public_row.get('title')}", ""]
        if public_row.get("deck"):
            lines += [str(public_row.get("deck")), ""]
        lines += ["## Summary", "", str(public_row.get("executive_summary") or ""), "", "## Key observations", ""]
        for claim in public_row.get("claims", []):
            lines.append(f"- {claim.get('text')}")
        lines += ["", "## Sources", ""]
        for source in public_row.get("evidence", []):
            url = source.get("source_url") or source.get("context_url") or ""
            lines.append(f"- {source.get('label')} — {url}" if url else f"- {source.get('label')}")
        lines += ["", "## Limitations", ""]
        for note in public_row.get("limitations", []):
            lines.append(f"- {note}")
        return "text/markdown", "\n".join(lines).strip() + "\n"

    def create_handoff(self, briefing_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        _reject_identity_payload(request)
        adapter = _safe_text(request.get("adapter") or "download", 80).lower()
        if adapter not in ALLOWED_HANDOFF_ADAPTERS:
            raise ValueError("Unsupported publication adapter.")
        briefing = self._briefing(briefing_id, public=False)
        if briefing.get("status") != "approved":
            raise ValueError("Only human-approved briefings may create publication handoffs.")
        now = self.now_fn().astimezone(timezone.utc)
        handoff = {
            "schema": HANDOFF_SCHEMA_VERSION,
            "release_version": APP_VERSION,
            "handoff_id": f"briefing-handoff:{uuid4().hex[:20]}",
            "briefing_id": briefing.get("briefing_id"),
            "adapter": adapter,
            "state": "ready_for_external_adapter" if adapter != "download" else "ready_for_download",
            "created_at": _iso(now),
            "payload": self._public_briefing(briefing),
            "publication_performed": False,
            "wordpress_write_performed": False,
            "provider_neutral": True,
            "recipient_data_included": False,
        }
        handoff["handoff_sha256"] = _digest({key: value for key, value in handoff.items() if key != "handoff_sha256"})
        _append(self.handoffs_path, handoff)
        return {"ok": True, "version": APP_VERSION, "handoff": handoff}

    def status(self) -> dict[str, Any]:
        rows = self.briefings(False, limit=500)
        packages = _latest(self.packages_path, "package_id", self.max_records)
        handoffs = _latest(self.handoffs_path, "handoff_id", self.max_records)
        return {
            "ok": True,
            "version": APP_VERSION,
            "schema": POLICY_SCHEMA_VERSION,
            "briefing_count": len(rows),
            "draft_count": sum(1 for row in rows if row.get("status") == "draft"),
            "approved_count": sum(1 for row in rows if row.get("status") == "approved"),
            "public_count": sum(1 for row in rows if row.get("published") is True),
            "package_count": len(packages),
            "handoff_count": len(handoffs),
            "automatic_publication": False,
            "automatic_wordpress_write": False,
        }

    def control_center(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": APP_VERSION,
            "policy": briefing_policy(),
            "templates": briefing_templates()["templates"],
            "status": self.status(),
            "briefings": self.briefings(False, limit=100),
            "human_review_required": True,
        }
