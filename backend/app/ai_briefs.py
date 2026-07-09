from __future__ import annotations

import json
import textwrap
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Sequence


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compact(value: Any, limit: int = 500) -> str:
    text = str(value or "").replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _list(value: Any, limit: int = 8) -> List[Any]:
    if isinstance(value, list):
        return value[:limit]
    if isinstance(value, tuple):
        return list(value[:limit])
    return []


def _as_text_list(items: Iterable[Any], limit: int = 8) -> List[str]:
    out: List[str] = []
    for item in items:
        if isinstance(item, str):
            text = item
        elif isinstance(item, Mapping):
            text = item.get("title") or item.get("summary") or item.get("recommendation") or item.get("action") or item.get("name") or item.get("path") or json.dumps(item, default=str)[:260]
        else:
            text = str(item)
        text = _compact(text, 320)
        if text and text not in out:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def _section_rows(report: Mapping[str, Any], section_ids: Sequence[str] | None = None, limit: int = 6) -> List[Any]:
    rows: List[Any] = []
    allowed = set(section_ids or [])
    for section in report.get("sections") or []:
        sid = str(section.get("section_id") or "")
        if allowed and sid not in allowed:
            continue
        for row in section.get("rows") or []:
            rows.append(row)
            if len(rows) >= limit:
                return rows
    return rows


def ai_status(settings: Any) -> Dict[str, Any]:
    provider = str(getattr(settings, "ai_provider", "disabled") or "disabled").lower()
    configured = False
    if provider == "gemini":
        configured = bool(getattr(settings, "gemini_api_key", ""))
    elif provider not in {"", "disabled", "none"}:
        configured = False
    enabled = provider not in {"", "disabled", "none"} and configured
    return {
        "ok": True,
        "provider": provider if provider else "disabled",
        "enabled": enabled,
        "configured": configured,
        "model": getattr(settings, "gemini_model", "gemini-1.5-flash") if provider == "gemini" else "deterministic-fallback",
        "mode": "ai-assisted" if enabled else "deterministic-fallback",
        "public_safe": True,
        "notes": [
            "AI assistance is disabled unless SC_SI_AI_PROVIDER and the matching provider key are configured.",
            "Deterministic fallback briefs are always available and do not call an external model.",
            "Brief endpoints are token-protected and intended for internal review unless explicitly marked public-safe.",
        ],
    }


def _report_focus(report: Mapping[str, Any], brief_type: str) -> Dict[str, Any]:
    report_id = str(report.get("report_id") or brief_type)
    focus_map = {
        "site-intelligence": {
            "title": "AI-Assisted Weekly Site Intelligence Brief",
            "summary": "Interpret the site-wide analytics, registry mapping, event readiness, and page-level recommendations.",
            "actions": [
                "Review high-visibility pages for stronger Workbench, Research Librarian, and GitHub pathways.",
                "Triage unmapped or inferred pages so the registry remains aligned with actual site behavior.",
                "Convert the strongest page movement into an internal planning note or LinkedIn/Substack candidate.",
            ],
            "risks": ["GA4 and registry signals are planning indicators; they should not be treated as complete user intent."],
        },
        "search": {
            "title": "AI-Assisted Search Intelligence Brief",
            "summary": "Interpret search visibility, query momentum, CTR opportunities, and article-map search performance.",
            "actions": [
                "Prioritize high-impression, low-CTR pages for title, excerpt, and internal-link improvements.",
                "Turn near-position search opportunities into targeted article updates and stronger gateway links.",
                "Use query clusters to decide which article maps deserve newsletter, LinkedIn, or repository support.",
            ],
            "risks": ["Search Console data can lag and should be reviewed across multiple periods before making major changes."],
        },
        "publishing": {
            "title": "AI-Assisted Publishing Strategy Brief",
            "summary": "Interpret update priorities, rising pages, decay signals, newsletter candidates, and promotion opportunities.",
            "actions": [
                "Select a small number of pages for immediate refresh rather than spreading work across the full library.",
                "Convert strong publishing candidates into LinkedIn posts, Substack briefs, or GitHub documentation updates.",
                "Use decay signals to identify pages that need new links, current examples, or clearer platform CTAs.",
            ],
            "risks": ["Publishing scores are directional and should be balanced with editorial judgment and strategic priorities."],
        },
        "external-sources": {
            "title": "AI-Assisted External Data Sources Brief",
            "summary": "Interpret connector health, fallback behavior, public-readiness, and external-source dashboard opportunities.",
            "actions": [
                "Keep public pages on cached or snapshot mode unless live connector latency is acceptable.",
                "Add optional provider keys only through Render environment variables and never in WordPress page content.",
                "Document source limits and review notes before publishing source-derived summaries.",
            ],
            "risks": ["External public APIs can change, fail, or rate limit; dashboard copy should disclose source and freshness limits."],
        },
        "public-dashboard": {
            "title": "AI-Assisted Public Dashboard Brief",
            "summary": "Interpret public-safe dashboard status, methodology notes, knowledge overview, and public release readiness.",
            "actions": [
                "Keep raw GA4, private recommendations, and conversion diagnostics off public pages.",
                "Use public dashboard text as a reviewed institutional summary, not as live operational telemetry.",
                "Pair public summaries with methodology notes and clear educational/analytical boundaries.",
            ],
            "risks": ["Public dashboards should use aggregated or sanitized outputs only."],
        },
    }
    return focus_map.get(brief_type) or focus_map.get(report_id) or focus_map["site-intelligence"]


def deterministic_brief(report: Mapping[str, Any], brief_type: str, mode: str = "private") -> Dict[str, Any]:
    focus = _report_focus(report, brief_type)
    highlights = _as_text_list(report.get("highlights") or [], limit=7)
    recommendations = _as_text_list(report.get("recommendations") or [], limit=8)
    key_rows = _as_text_list(_section_rows(report, limit=8), limit=8)
    executive_parts = []
    if report.get("summary"):
        executive_parts.append(_compact(report.get("summary"), 420))
    if highlights:
        executive_parts.append("Key signal: " + highlights[0])
    if recommendations:
        executive_parts.append("Primary action: " + recommendations[0])
    if not executive_parts:
        executive_parts.append(focus["summary"])

    recommended_actions = recommendations[:5] + [item for item in focus["actions"] if item not in recommendations]
    content_opportunities = key_rows[:5]
    if not content_opportunities:
        content_opportunities = [
            "Use this brief to decide which pages, article maps, public dashboard sections, or repository notes deserve attention next."
        ]

    public_safe_summary = " ".join(executive_parts[:2])
    brief = {
        "ok": True,
        "brief_id": f"{brief_type}-ai-brief",
        "title": focus["title"],
        "summary": focus["summary"],
        "generated_at": utc_now(),
        "mode": mode,
        "provider": "deterministic-fallback",
        "model": "rules-v0.8.0",
        "source_report": {
            "report_id": report.get("report_id"),
            "title": report.get("title"),
            "generated_at": report.get("generated_at"),
            "source": report.get("source"),
            "date_range": report.get("date_range") or {},
        },
        "executive_summary": " ".join(executive_parts),
        "key_findings": highlights or [focus["summary"]],
        "recommended_actions": recommended_actions[:8],
        "content_opportunities": content_opportunities,
        "risk_notes": list(focus["risks"]) + _as_text_list((report.get("methodology") or {}).values(), limit=2),
        "public_safe_summary": _compact(public_safe_summary, 800),
        "private_notes": [] if mode == "public" else [
            "This is an internal planning brief. Review before reusing language publicly.",
            "Use public dashboard endpoints for public pages; keep raw analytics/report details private unless reviewed.",
        ],
        "confidence": {
            "level": "medium" if highlights or recommendations else "low",
            "basis": "Generated from structured Site Intelligence report highlights, recommendations, and report sections.",
        },
        "sections": [
            {"section_id": "executive_summary", "title": "Executive summary", "rows": [" ".join(executive_parts)]},
            {"section_id": "actions", "title": "Recommended next actions", "rows": recommended_actions[:8]},
            {"section_id": "opportunities", "title": "Content and platform opportunities", "rows": content_opportunities[:8]},
            {"section_id": "risks", "title": "Risk and uncertainty notes", "rows": list(focus["risks"])},
        ],
        "methodology": {
            "summary": "v0.8.0 briefs use deterministic interpretation unless an optional AI provider is explicitly configured.",
            "privacy_note": "The default brief mode is internal/private. Public summaries should be manually reviewed before publication.",
        },
    }
    return brief


def _extract_json_object(text: str) -> Dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    candidates = [text]
    if "```" in text:
        parts = text.split("```")
        candidates.extend(part for part in parts if "{" in part and "}" in part)
    for candidate in candidates:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            continue
        try:
            parsed = json.loads(candidate[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return None


def _gemini_generate(settings: Any, prompt: str) -> str:
    model = getattr(settings, "gemini_model", "gemini-1.5-flash") or "gemini-1.5-flash"
    key = getattr(settings, "gemini_api_key", "")
    if not key:
        raise RuntimeError("Gemini API key is not configured.")
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": float(getattr(settings, "ai_temperature", 0.2)),
            "maxOutputTokens": int(getattr(settings, "ai_max_output_tokens", 1200)),
            "responseMimeType": "application/json",
        },
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    timeout = int(getattr(settings, "ai_timeout_seconds", 12))
    with urllib.request.urlopen(req, timeout=timeout) as response:  # nosec B310 - endpoint is fixed Google Gemini API URL.
        data = json.loads(response.read().decode("utf-8"))
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates.")
    parts = ((candidates[0].get("content") or {}).get("parts") or [])
    text = "\n".join(str(part.get("text", "")) for part in parts if isinstance(part, Mapping)).strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text


def _ai_prompt(report: Mapping[str, Any], brief_type: str, mode: str, fallback: Mapping[str, Any]) -> str:
    slim_report = {
        "report_id": report.get("report_id"),
        "title": report.get("title"),
        "summary": report.get("summary"),
        "date_range": report.get("date_range"),
        "highlights": _list(report.get("highlights"), 8),
        "recommendations": _list(report.get("recommendations"), 8),
        "sections": [],
    }
    for section in report.get("sections") or []:
        slim_report["sections"].append({
            "section_id": section.get("section_id"),
            "title": section.get("title"),
            "summary": section.get("summary"),
            "metrics": section.get("metrics"),
            "rows": _list(section.get("rows"), 5),
        })
        if len(slim_report["sections"]) >= 5:
            break
    schema = {
        "executive_summary": "one paragraph",
        "key_findings": ["3-6 findings"],
        "recommended_actions": ["4-8 actions"],
        "content_opportunities": ["3-6 opportunities"],
        "risk_notes": ["2-5 uncertainty or public-safety notes"],
        "public_safe_summary": "short public-safe summary",
        "confidence": {"level": "low|medium|high", "basis": "why"},
    }
    return textwrap.dedent(f"""
    You are producing an internal Sustainable Catalyst Site Intelligence brief.
    Interpret the report, but do not invent metrics or claims not present in the source payload.
    The brief type is {brief_type!r}. The requested mode is {mode!r}.
    Keep public-facing language cautious and avoid exposing raw private analytics in public_safe_summary.
    Return ONLY valid JSON matching this schema:
    {json.dumps(schema)}

    Source report:
    {json.dumps(slim_report, default=str)[:12000]}

    Deterministic fallback for reference:
    {json.dumps({k: fallback.get(k) for k in ['executive_summary','key_findings','recommended_actions','content_opportunities','risk_notes','public_safe_summary','confidence']}, default=str)[:6000]}
    """).strip()


def build_ai_brief(report: Mapping[str, Any], brief_type: str, settings: Any, mode: str = "private", use_ai: bool = True) -> Dict[str, Any]:
    mode = "public" if str(mode).lower() == "public" else "private"
    fallback = deterministic_brief(report, brief_type, mode=mode)
    status = ai_status(settings)
    if not use_ai or not status.get("enabled"):
        fallback["ai_status"] = status
        fallback["provider"] = status.get("provider", "deterministic-fallback")
        fallback["model"] = status.get("model", "rules-v0.8.0")
        fallback["methodology"]["summary"] = "Generated with deterministic fallback because the AI provider is disabled or not configured."
        return fallback

    provider = status.get("provider")
    try:
        if provider == "gemini":
            text = _gemini_generate(settings, _ai_prompt(report, brief_type, mode, fallback))
        else:
            raise RuntimeError(f"Unsupported AI provider: {provider}")
        parsed = _extract_json_object(text)
        if not parsed:
            raise RuntimeError("AI response was not valid JSON.")
        brief = dict(fallback)
        for key in ["executive_summary", "key_findings", "recommended_actions", "content_opportunities", "risk_notes", "public_safe_summary", "confidence"]:
            if key in parsed:
                brief[key] = parsed[key]
        brief["provider"] = provider
        brief["model"] = status.get("model")
        brief["ai_status"] = status
        brief["ai_metadata"] = {"generated_by_provider": True, "fallback_available": True}
        brief["sections"] = [
            {"section_id": "executive_summary", "title": "Executive summary", "rows": [brief.get("executive_summary", "")]},
            {"section_id": "actions", "title": "Recommended next actions", "rows": brief.get("recommended_actions") or []},
            {"section_id": "opportunities", "title": "Content and platform opportunities", "rows": brief.get("content_opportunities") or []},
            {"section_id": "risks", "title": "Risk and uncertainty notes", "rows": brief.get("risk_notes") or []},
        ]
        return brief
    except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        fallback["ai_status"] = status
        fallback["ai_error"] = {"error_type": exc.__class__.__name__, "message": str(exc)}
        fallback["methodology"]["summary"] = "Generated with deterministic fallback because the configured AI provider failed or timed out."
        return fallback
