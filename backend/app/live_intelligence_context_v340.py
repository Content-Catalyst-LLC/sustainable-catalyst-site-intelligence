"""Signal context, evidence, and drill-down support for Site Intelligence v3.13.0.

The module builds public-safe detail records around already-selected Live
Intelligence signals. It preserves source identity, timestamps, ranking
explanations, uncertainty, and limitations. It does not add hidden facts,
claim independent verification, or turn a ticker signal into emergency,
medical, legal, or financial advice.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
import re
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import quote

from .version import APP_VERSION

CONTEXT_SCHEMA_VERSION = "sc-site-intelligence-live-signal-context/1.0"
EVIDENCE_SCHEMA_VERSION = "sc-site-intelligence-live-signal-evidence/1.0"
CONTEXT_POLICY_SCHEMA_VERSION = "sc-site-intelligence-live-signal-context-policy/1.0"

FeedBuilder = Callable[..., dict[str, Any]]

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "the", "to", "with", "updated", "latest",
    "open", "current", "report", "reports", "data", "signal", "intelligence",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value: Any, limit: int = 500) -> str:
    return " ".join(str(value or "").split())[:limit]


def _tokens(*values: Any) -> set[str]:
    text = " ".join(_clean(value, 500).lower() for value in values)
    words = re.findall(r"[a-z0-9][a-z0-9'-]{2,}", text)
    return {word for word in words if word not in _STOPWORDS}


def _safe_url(value: Any) -> str:
    candidate = str(value or "").strip()
    return candidate if candidate.startswith(("https://", "http://", "/")) else ""


def _encoded_signal_id(signal_id: str) -> str:
    return quote(str(signal_id or ""), safe="")


def enrich_signal_links(signals: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Attach stable context and evidence routes without changing source links."""
    output: list[dict[str, Any]] = []
    for item in signals:
        signal = dict(item)
        signal_id = str(signal.get("signal_id") or "").strip()
        if signal_id:
            encoded = _encoded_signal_id(signal_id)
            signal.update({
                "context_available": True,
                "context_url": f"/public/live-intelligence/signals/{encoded}",
                "context_view_url": f"/public/live-intelligence/signals/{encoded}/view",
                "evidence_url": f"/public/live-intelligence/signals/{encoded}/evidence",
            })
        else:
            signal["context_available"] = False
        output.append(signal)
    return output


def _source_records(signal: Mapping[str, Any]) -> list[dict[str, Any]]:
    names = [str(signal.get("source_name") or "Public source")]
    names.extend(str(value) for value in (signal.get("corroborating_sources") or []) if value)
    urls = [str(signal.get("source_url") or "")]
    urls.extend(str(value) for value in (signal.get("cluster_source_urls") or []) if value)
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, name in enumerate(names):
        url = _safe_url(urls[index] if index < len(urls) else "")
        key = (_clean(name, 120), url)
        if not key[0] or key in seen:
            continue
        seen.add(key)
        records.append({
            "name": key[0],
            "url": url,
            "role": "primary" if index == 0 else "represented",
            "independent_verification_claimed": False,
        })
    return records


def _timeline(signal: Mapping[str, Any], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidates = [
        ("observed", signal.get("observed_at"), "Source observation or publication time"),
        ("updated", signal.get("updated_at"), "Most recent source or connector update"),
        ("selected", generated_at, "Selected for the current Live Intelligence response"),
    ]
    seen: set[tuple[str, str]] = set()
    for state, timestamp, label in candidates:
        value = str(timestamp or "").strip()
        if not value or (state, value) in seen:
            continue
        seen.add((state, value))
        rows.append({"state": state, "timestamp": value, "label": label})
    return rows


def _location(signal: Mapping[str, Any]) -> dict[str, Any]:
    coords = signal.get("coordinates")
    longitude = latitude = None
    if isinstance(coords, (list, tuple)) and len(coords) >= 2:
        try:
            longitude = float(coords[0])
            latitude = float(coords[1])
        except (TypeError, ValueError):
            longitude = latitude = None
    label = _clean(
        signal.get("location_label") or signal.get("country") or signal.get("region") or "",
        160,
    )
    map_url = ""
    if longitude is not None and latitude is not None:
        map_url = f"https://www.openstreetmap.org/?mlat={latitude:.6f}&mlon={longitude:.6f}#map=6/{latitude:.6f}/{longitude:.6f}"
    return {
        "available": bool(label or map_url),
        "label": label,
        "country": _clean(signal.get("country"), 100),
        "country_code": _clean(signal.get("country_code"), 12).upper(),
        "region": _clean(signal.get("region"), 100),
        "longitude": longitude,
        "latitude": latitude,
        "map_url": map_url,
        "precision_note": "Coordinates reflect the source record and may be approximate." if map_url else "No map coordinates were provided by the selected signal.",
    }


def _related_routes(signal: Mapping[str, Any]) -> list[dict[str, str]]:
    category = str(signal.get("category") or "")
    routes: dict[str, list[tuple[str, str, str]]] = {
        "earth_systems": [
            ("Earth Observation Studio", "/app/?view=earth", "Inspect environmental and Earth-observation context."),
            ("Spatial Evidence Studio", "/app/?view=spatial", "Review mapped public evidence and geographic limitations."),
            ("Public Observatories", "/app/?view=observatory", "Inspect source, lineage, and audit context."),
        ],
        "human_systems": [
            ("Humanitarian Observatory", "/app/?view=humanitarian", "Review humanitarian and displacement context."),
            ("Country Intelligence", "/app/?view=country", "Open the relevant country or regional dossier workflow."),
            ("Public Observatories", "/app/?view=observatory", "Inspect source and evidence lineage."),
        ],
        "research": [
            ("Research Paths", "/app/?view=research", "Continue into a saved investigation or briefing workflow."),
            ("Sources + Methodology", "/app/?view=sources", "Inspect publisher, connector, and method context."),
            ("Public Observatories", "/app/?view=observatory", "Review evidence and release history."),
        ],
        "economy_resources": [
            ("Economics and Sustainability", "/app/?view=economics", "Inspect economic, development, and sustainability indicators."),
            ("Trade, Energy and Resources", "/app/?view=resources", "Review resource-security and dependency context."),
            ("Country Intelligence", "/app/?view=country", "Compare the signal with country-level evidence."),
        ],
        "platform": [
            ("Connected Intelligence", "/app/?view=overview", "Open the full connected public-intelligence workspace."),
            ("Sources + Methodology", "/app/?view=sources", "Review source and connector status."),
        ],
    }
    return [
        {"label": label, "url": url, "description": description}
        for label, url, description in routes.get(category, routes["platform"])
    ]


def _related_research(signal: Mapping[str, Any], signals: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    target = _tokens(signal.get("label"), signal.get("value"), signal.get("detail"), signal.get("location_label"))
    candidates: list[tuple[int, dict[str, Any]]] = []
    for item in signals:
        if str(item.get("category") or "") != "research" or item.get("signal_id") == signal.get("signal_id"):
            continue
        overlap = len(target & _tokens(item.get("label"), item.get("value"), item.get("detail")))
        if overlap <= 0:
            continue
        candidates.append((overlap, {
            "signal_id": str(item.get("signal_id") or ""),
            "title": _clean(item.get("value") or item.get("label"), 220),
            "source": _clean(item.get("source_name"), 120),
            "url": _safe_url(item.get("destination_url") or item.get("source_url")),
            "shared_terms": overlap,
            "relationship_note": "Keyword overlap only; this does not establish relevance, causation, or endorsement.",
        }))
    candidates.sort(key=lambda row: (-row[0], row[1]["title"]))
    return [row[1] for row in candidates[:3]]


def _evidence_record(signal: Mapping[str, Any], generated_at: str) -> dict[str, Any]:
    record = {
        "schema": EVIDENCE_SCHEMA_VERSION,
        "version": APP_VERSION,
        "generated_at": generated_at,
        "signal_id": str(signal.get("signal_id") or ""),
        "cluster_id": str(signal.get("cluster_id") or ""),
        "category": str(signal.get("category") or ""),
        "feed_id": str(signal.get("feed_id") or ""),
        "label": _clean(signal.get("label"), 120),
        "value": _clean(signal.get("value"), 240),
        "detail": _clean(signal.get("detail"), 800),
        "status": str(signal.get("status") or ""),
        "data_state": str(signal.get("data_state") or ""),
        "development_state": str(signal.get("development_state") or ""),
        "observed_at": str(signal.get("observed_at") or ""),
        "updated_at": str(signal.get("updated_at") or ""),
        "source_records": _source_records(signal),
        "location": _location(signal),
        "selection": {
            "rank": int(signal.get("selection_rank") or 0),
            "score": int(signal.get("selection_score") or 0),
            "reasons": list(signal.get("selection_reasons") or []),
            "components": dict(signal.get("ranking_components") or {}),
        },
        "cluster": {
            "size": int(signal.get("cluster_size") or 1),
            "source_count": int(signal.get("cluster_source_count") or 1),
            "member_ids": list(signal.get("cluster_member_ids") or []),
            "reason": _clean(signal.get("cluster_reason"), 240),
            "confidence": float(signal.get("cluster_confidence") or 0.0),
        },
        "boundaries": [
            "This record preserves the selected public signal and its source metadata; it is not an independent verification certificate.",
            "Display rank is not a truth, danger, accuracy, or institutional-importance score.",
            "Use official source notices for emergency, legal, medical, or financial decisions.",
        ],
    }
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    record["integrity"] = {
        "algorithm": "sha256",
        "canonical_digest": sha256(canonical.encode("utf-8")).hexdigest(),
        "scope": "public-safe evidence record before integrity block",
    }
    return record


def build_signal_context(settings: Any, signal_id: str, feed_builder: FeedBuilder) -> dict[str, Any]:
    """Build a public-safe context packet for a current Live Intelligence signal."""
    signal_id = str(signal_id or "").strip()
    if not signal_id:
        raise KeyError("Signal not found")
    feed = feed_builder(settings, limit=24, max_per_source=5, record_operations=False)
    signals = enrich_signal_links(feed.get("signals") or [])
    signal = next((item for item in signals if str(item.get("signal_id") or "") == signal_id), None)
    if signal is None:
        raise KeyError(signal_id)
    generated_at = _now()
    evidence = _evidence_record(signal, generated_at)
    context = {
        "ok": True,
        "version": APP_VERSION,
        "schema": CONTEXT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "signal": signal,
        "headline": _clean(signal.get("value") or signal.get("label"), 240),
        "summary": _clean(signal.get("detail") or signal.get("value") or signal.get("label"), 800),
        "classification": {
            "category": str(signal.get("category") or ""),
            "feed_id": str(signal.get("feed_id") or ""),
            "status": str(signal.get("status") or ""),
            "severity": str(signal.get("severity") or ""),
            "data_state": str(signal.get("data_state") or ""),
            "development_state": str(signal.get("development_state") or ""),
        },
        "selection": evidence["selection"],
        "sources": evidence["source_records"],
        "timeline": _timeline(signal, str(feed.get("generated_at") or generated_at)),
        "location": evidence["location"],
        "related_routes": _related_routes(signal),
        "related_research": _related_research(signal, signals),
        "methodology": {
            "clustering": _clean(signal.get("cluster_reason") or "This signal represents one selected source record.", 300),
            "ranking": "Signals are ranked for display relevance using transparent significance, freshness, source-priority, corroboration, editorial-priority, and data-state components.",
            "source_handling": "Source names, links, update times, represented-source counts, and data state remain visible.",
            "limitations": [
                "Context is assembled from the current Live Intelligence response and may change as public sources update.",
                "Related research is selected only through visible term overlap and is not a claim of substantive relevance.",
                "Map coordinates may be approximate and should be checked against the original source.",
            ],
        },
        "actions": {
            "source_url": _safe_url(signal.get("source_url") or signal.get("destination_url")),
            "open_site_intelligence": f"/app/?view=events&signal={_encoded_signal_id(signal_id)}",
            "decision_studio_handoff": f"/platform/decision-studio/?source=live-intelligence&signal={_encoded_signal_id(signal_id)}",
            "evidence_url": str(signal.get("evidence_url") or ""),
            "context_view_url": str(signal.get("context_view_url") or ""),
        },
        "evidence": evidence,
        "boundaries": evidence["boundaries"],
    }
    return context


def build_signal_evidence(settings: Any, signal_id: str, feed_builder: FeedBuilder) -> dict[str, Any]:
    return build_signal_context(settings, signal_id, feed_builder)["evidence"]


def context_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": CONTEXT_POLICY_SCHEMA_VERSION,
        "capabilities": [
            "signal detail records",
            "source lineage",
            "event timeline",
            "map context when coordinates exist",
            "related workspace routes",
            "term-overlap research suggestions",
            "downloadable evidence records with SHA-256 digest",
            "Site Intelligence and Decision Studio handoffs",
        ],
        "boundaries": [
            "Context pages do not independently verify a source claim.",
            "Related records and research do not establish causation, endorsement, or completeness.",
            "Maps preserve source coordinates and do not increase geographic precision.",
            "Evidence digests verify packet integrity, not factual truth.",
            "Human review remains required before publication or consequential use.",
        ],
    }


def render_signal_context_html(context: Mapping[str, Any]) -> str:
    """Render a standalone accessible detail view for direct backend use."""
    signal = context.get("signal") or {}
    location = context.get("location") or {}
    sources = context.get("sources") or []
    timeline = context.get("timeline") or []
    routes = context.get("related_routes") or []
    research = context.get("related_research") or []
    source_html = "".join(
        f'<li><a href="{escape(str(item.get("url") or "#"))}">{escape(str(item.get("name") or "Public source"))}</a> <small>{escape(str(item.get("role") or ""))}</small></li>'
        if item.get("url") else f'<li>{escape(str(item.get("name") or "Public source"))}</li>'
        for item in sources
    ) or "<li>No source link was returned.</li>"
    timeline_html = "".join(
        f'<li><strong>{escape(str(item.get("label") or item.get("state") or "Update"))}</strong><br><time>{escape(str(item.get("timestamp") or ""))}</time></li>'
        for item in timeline
    )
    routes_html = "".join(
        f'<li><a href="{escape(str(item.get("url") or "#"))}">{escape(str(item.get("label") or "Workspace"))}</a> — {escape(str(item.get("description") or ""))}</li>'
        for item in routes
    )
    research_html = "".join(
        f'<li><a href="{escape(str(item.get("url") or "#"))}">{escape(str(item.get("title") or "Research record"))}</a><br><small>{escape(str(item.get("relationship_note") or ""))}</small></li>'
        for item in research
    ) or "<li>No term-overlap research signal was selected in the current feed.</li>"
    map_html = ""
    if location.get("available"):
        label = escape(str(location.get("label") or "Mapped source location"))
        map_link = escape(str(location.get("map_url") or ""))
        map_html = f'<section><h2>Location</h2><p>{label}</p>'
        if map_link:
            map_html += f'<p><a href="{map_link}" rel="noopener noreferrer">Open map</a></p>'
        map_html += f'<p><small>{escape(str(location.get("precision_note") or ""))}</small></p></section>'
    evidence_url = escape(str((context.get("actions") or {}).get("evidence_url") or "#"))
    source_url = escape(str((context.get("actions") or {}).get("source_url") or ""))
    source_action = f'<a class="button" href="{source_url}">Open primary source</a>' if source_url else ""
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(str(context.get("headline") or "Live Intelligence signal"))} — Site Intelligence</title>
<style>body{{font-family:system-ui,sans-serif;margin:0;background:#f5f5f2;color:#171717}}main{{max-width:980px;margin:auto;padding:2rem}}article,section{{background:#fff;border:1px solid #d8d8d2;padding:1.25rem;margin:1rem 0}}.eyebrow{{text-transform:uppercase;letter-spacing:.08em;font-weight:700}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem}}a{{color:#5b172d}}.button{{display:inline-block;padding:.65rem .9rem;border:1px solid currentColor;margin:.25rem .5rem .25rem 0}}small{{color:#555}}code{{overflow-wrap:anywhere}}</style></head>
<body><main><p class="eyebrow">Live Intelligence · Signal Context</p><h1>{escape(str(context.get("headline") or signal.get("label") or "Live signal"))}</h1><p>{escape(str(context.get("summary") or ""))}</p>
<p>{source_action}<a class="button" href="{evidence_url}">Open evidence record</a></p>
<div class="grid"><section><h2>Classification</h2><p>Category: {escape(str(signal.get("category") or ""))}<br>Status: {escape(str(signal.get("status") or ""))}<br>State: {escape(str(signal.get("development_state") or ""))}</p></section><section><h2>Selection context</h2><p>Rank {escape(str(signal.get("selection_rank") or ""))} · Score {escape(str(signal.get("selection_score") or ""))}</p><p>{escape('; '.join(signal.get("selection_reasons") or []))}</p></section></div>
<section><h2>Sources</h2><ul>{source_html}</ul></section><section><h2>Timeline</h2><ol>{timeline_html}</ol></section>{map_html}<section><h2>Continue in Site Intelligence</h2><ul>{routes_html}</ul></section><section><h2>Related research</h2><ul>{research_html}</ul></section><section><h2>Method and limitations</h2><ul>{''.join(f'<li>{escape(str(value))}</li>' for value in context.get('boundaries') or [])}</ul></section>
<p><small>Signal ID: <code>{escape(str(signal.get("signal_id") or ""))}</code> · Context generated {escape(str(context.get("generated_at") or ""))}</small></p></main></body></html>'''
