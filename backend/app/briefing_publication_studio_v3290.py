"""Briefing, Story Map, and Publication Studio contracts for Site Intelligence v4.26.0.

Public endpoints are deterministic preview/export contracts. They do not mutate the
existing publishing store and cannot publish, correct, retract, or hand off content.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import csv
import html
import io
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .version import APP_VERSION

SCHEMA = "sc-site-intelligence-briefing-publication-studio/1.0"
RELEASE_ID = f"site-intelligence-v{APP_VERSION}"
POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "briefing_publication_policy_v3290.json"
_SECRET = re.compile(r"(?:password|secret|token|authorization|cookie|session|api[_-]?key|email|phone|user[_-]?id|person[_-]?id)", re.I)
_URL = re.compile(r"^https?://", re.I)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _text(value: Any, limit: int = 2000) -> str:
    return str(value or "").strip()[:limit]


def _items(value: Any, maximum: int = 500) -> list[Any]:
    return list(value[:maximum]) if isinstance(value, list) else []


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return sha256(_canonical(value)).hexdigest()


def _scan(value: Any, path: str = "request") -> list[str]:
    issues: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _SECRET.search(str(key)):
                issues.append(f"{path}.{key} is not permitted in a public publication package")
            issues.extend(_scan(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for i, child in enumerate(value[:1000]):
            issues.extend(_scan(child, f"{path}[{i}]"))
    return issues


def _source(raw: Mapping[str, Any], index: int) -> dict[str, Any]:
    url = _text(raw.get("source_url") or raw.get("url"), 1200)
    if url and not _URL.match(url):
        url = ""
    row = {
        "source_id": _text(raw.get("source_id") or raw.get("id") or f"source-{index+1}", 180),
        "publisher": _text(raw.get("publisher") or raw.get("source") or "Unknown publisher", 300),
        "title": _text(raw.get("title") or raw.get("name") or "Public source", 500),
        "source_url": url,
        "observed_at": _text(raw.get("observed_at") or raw.get("period"), 120),
        "retrieved_at": _text(raw.get("retrieved_at") or raw.get("captured_at"), 120),
        "truth_state": _text(raw.get("truth_state") or raw.get("freshness") or "unknown", 80).lower(),
        "limitations": [_text(x, 600) for x in _items(raw.get("limitations"), 40) if _text(x, 600)],
    }
    row["record_sha256"] = _digest(row)
    return row


def _evidence(raw: Mapping[str, Any], index: int) -> dict[str, Any]:
    row = {
        "evidence_id": _text(raw.get("evidence_id") or raw.get("record_id") or raw.get("id") or f"evidence-{index+1}", 180),
        "title": _text(raw.get("title") or raw.get("name") or "Evidence record", 500),
        "source_id": _text(raw.get("source_id") or raw.get("source"), 180),
        "country": _text(raw.get("country") or raw.get("country_code"), 12).upper(),
        "indicator_id": _text(raw.get("indicator_id") or raw.get("metric"), 180),
        "value": raw.get("value"),
        "unit": _text(raw.get("unit"), 80),
        "observed_at": _text(raw.get("observed_at") or raw.get("period"), 120),
        "truth_state": _text(raw.get("truth_state") or raw.get("freshness") or "unknown", 80).lower(),
        "limitations": [_text(x, 600) for x in _items(raw.get("limitations"), 40) if _text(x, 600)],
    }
    row["record_sha256"] = _digest(row)
    return row


def _block(raw: Mapping[str, Any], index: int) -> dict[str, Any]:
    block_type = _text(raw.get("block_type") or raw.get("type") or "narrative", 80).lower()
    allowed = {"narrative", "heading", "callout", "map", "timeline", "chart", "evidence_table", "source_list", "methodology", "limitations", "image", "divider"}
    if block_type not in allowed:
        block_type = "narrative"
    row = {
        "block_id": _text(raw.get("block_id") or raw.get("id") or f"block-{index+1}", 180),
        "block_type": block_type,
        "position": int(raw.get("position") or index + 1),
        "title": _text(raw.get("title"), 500),
        "text": _text(raw.get("text") or (raw.get("content") or {}).get("text") if isinstance(raw.get("content"), Mapping) else raw.get("text"), 12000),
        "source_ids": [_text(x, 180) for x in _items(raw.get("source_ids"), 200) if _text(x, 180)],
        "evidence_ids": [_text(x, 180) for x in _items(raw.get("evidence_ids"), 200) if _text(x, 180)],
        "alt_text": _text(raw.get("alt_text"), 1000),
        "caption": _text(raw.get("caption"), 2000),
    }
    row["block_sha256"] = _digest(row)
    return row


class BriefingPublicationStudio:
    def __init__(self) -> None:
        self.policy = _policy()

    def schema(self) -> dict[str, Any]:
        return {
            "ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA,
            "contract": "briefing-story-map-publication-studio",
            "publication_types": list(self.policy["publication_types"]),
            "correction_actions": list(self.policy["correction_actions"]),
            "export_formats": list(self.policy["export_formats"]),
            "human_editorial_review_required": True,
            "human_publish_confirmation_required": True,
            "automatic_publication": False,
            "public_write_performed": False,
            "boundaries": list(self.policy["principles"]),
        }

    def freeze_manifest(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        issues = _scan(request)
        if issues:
            raise ValueError("; ".join(issues[:5]))
        sources = [_source(x, i) for i, x in enumerate(_items(request.get("sources"), 500)) if isinstance(x, Mapping)]
        evidence = [_evidence(x, i) for i, x in enumerate(_items(request.get("evidence"), 1000)) if isinstance(x, Mapping)]
        manifest = {
            "schema": "sc-site-intelligence-frozen-evidence-manifest/1.0",
            "version": APP_VERSION,
            "frozen_at": _text(request.get("frozen_at") or _now(), 120),
            "sources": sources,
            "evidence": evidence,
            "source_count": len(sources),
            "evidence_count": len(evidence),
            "missing_source_urls": [s["source_id"] for s in sources if not s["source_url"]],
            "truth_states": sorted({x["truth_state"] for x in sources + evidence}),
            "proof_of_accuracy": False,
            "change_detection_only": True,
        }
        manifest["manifest_sha256"] = _digest({k: v for k, v in manifest.items() if k != "manifest_sha256"})
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA, "contract": "frozen-evidence-manifest", "manifest": manifest}

    def briefing(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        issues = _scan(request)
        if issues:
            raise ValueError("; ".join(issues[:5]))
        title = _text(request.get("title"), 500)
        if not title:
            raise ValueError("title is required")
        methodology = [_text(x, 2000) for x in _items(request.get("methodology"), 100) if _text(x, 2000)]
        limitations = [_text(x, 2000) for x in _items(request.get("limitations"), 100) if _text(x, 2000)]
        blocks = [_block(x, i) for i, x in enumerate(_items(request.get("blocks"), 200)) if isinstance(x, Mapping)]
        if not blocks:
            blocks = [_block({"block_type": "narrative", "title": "Summary", "text": _text(request.get("summary"), 12000)}, 0)]
        frozen = self.freeze_manifest(request).get("manifest")
        publication_type = _text(request.get("publication_type") or "intelligence-brief", 100)
        if publication_type not in self.policy["publication_types"]:
            publication_type = "intelligence-brief"
        brief = {
            "schema": "sc-site-intelligence-briefing-preview/1.0",
            "version": APP_VERSION,
            "title": title,
            "subtitle": _text(request.get("subtitle"), 1000),
            "summary": _text(request.get("summary"), 8000),
            "publication_type": publication_type,
            "authors": [_text(x, 300) for x in _items(request.get("authors"), 30) if _text(x, 300)],
            "topics": [_text(x, 200) for x in _items(request.get("topics"), 100) if _text(x, 200)],
            "geographies": [_text(x, 200) for x in _items(request.get("geographies"), 100) if _text(x, 200)],
            "blocks": blocks,
            "methodology": methodology,
            "limitations": limitations,
            "frozen_manifest": frozen,
            "editorial_state": "draft",
            "human_review_required": True,
            "human_publish_confirmation_required": True,
            "automatic_publication": False,
            "write_performed": False,
        }
        brief["brief_sha256"] = _digest({k: v for k, v in brief.items() if k != "brief_sha256"})
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA, "contract": "briefing-preview", "brief": brief}

    def story_map(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        brief = self.briefing({**dict(request or {}), "publication_type": "story-map"})["brief"]
        blocks = [b for b in brief["blocks"] if b["block_type"] in {"heading", "narrative", "callout", "map", "timeline", "chart", "image"}]
        accessibility = self._accessibility(blocks)
        story = {
            "schema": "sc-site-intelligence-story-map-preview/1.0", "version": APP_VERSION,
            "title": brief["title"], "blocks": blocks, "frozen_manifest": brief["frozen_manifest"],
            "accessibility": accessibility,
            "interpretation_boundary": "Story sequence, map proximity, chart alignment, and temporal adjacency do not establish causation.",
            "editorial_state": "draft", "automatic_publication": False, "write_performed": False,
        }
        story["story_map_sha256"] = _digest({k: v for k, v in story.items() if k != "story_map_sha256"})
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA, "contract": "story-map-preview", "story_map": story}

    def _accessibility(self, blocks: list[dict[str, Any]]) -> dict[str, Any]:
        missing_alt = [b["block_id"] for b in blocks if b["block_type"] in {"image", "map", "chart"} and not b["alt_text"]]
        untitled_visuals = [b["block_id"] for b in blocks if b["block_type"] in {"image", "map", "chart"} and not b["title"]]
        return {
            "status": "pass" if not missing_alt and not untitled_visuals else "needs-review",
            "missing_alt_text": missing_alt, "untitled_visuals": untitled_visuals,
            "semantic_html_required": True, "keyboard_order_required": True,
        }

    def readiness(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        brief = self.briefing(request)["brief"]
        checks = {
            "title": bool(brief["title"]),
            "summary": bool(brief["summary"]),
            "methodology": bool(brief["methodology"]),
            "limitations": bool(brief["limitations"]),
            "evidence_manifest": bool(brief["frozen_manifest"]["evidence_count"] or brief["frozen_manifest"]["source_count"]),
            "visual_accessibility": self._accessibility(brief["blocks"])["status"] == "pass",
        }
        return {
            "ok": True, "version": APP_VERSION, "schema": SCHEMA, "contract": "publication-readiness",
            "status": "ready-for-human-review" if all(checks.values()) else "incomplete",
            "checks": checks, "human_review_still_required": True, "publish_allowed": False,
            "brief_sha256": brief["brief_sha256"],
        }

    def correction(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        issues = _scan(request)
        if issues:
            raise ValueError("; ".join(issues[:5]))
        publication_id = _text(request.get("publication_id"), 180)
        version_id = _text(request.get("version_id"), 180)
        note = _text(request.get("note") or request.get("correction_note"), 5000)
        action = _text(request.get("action") or "correction", 40).lower()
        if not publication_id or not version_id or not note:
            raise ValueError("publication_id, version_id, and correction note are required")
        if action not in self.policy["correction_actions"]:
            raise ValueError("unsupported correction action")
        correction = {
            "schema": "sc-site-intelligence-publication-correction-preview/1.0", "version": APP_VERSION,
            "publication_id": publication_id, "version_id": version_id, "action": action,
            "note": note, "reason": _text(request.get("reason"), 2000), "prepared_at": _now(),
            "preserves_prior_version": True, "human_review_required": True,
            "automatic_change": False, "write_performed": False,
        }
        correction["correction_sha256"] = _digest({k: v for k, v in correction.items() if k != "correction_sha256"})
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA, "contract": "correction-preview", "correction": correction}

    def package(self, request: Mapping[str, Any] | None = None) -> dict[str, Any]:
        brief = self.briefing(request)["brief"]
        access = self._accessibility(brief["blocks"])
        md = [f"# {brief['title']}"]
        if brief["summary"]:
            md += ["", brief["summary"]]
        for block in brief["blocks"]:
            if block["title"]:
                md += ["", f"## {block['title']}"]
            if block["text"]:
                md += ["", block["text"]]
        md += ["", "## Methodology"] + [f"- {x}" for x in brief["methodology"]]
        md += ["", "## Limitations"] + [f"- {x}" for x in brief["limitations"]]
        sections = []
        for block in brief["blocks"]:
            sections.append(f'<section data-type="{html.escape(block["block_type"])}"><h2>{html.escape(block["title"] or block["block_type"].replace("_", " ").title())}</h2><p>{html.escape(block["text"])}</p></section>')
        print_html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{}</title></head><body><main><article><h1>{}</h1><p>{}</p>{}<section><h2>Methodology</h2>{}</section><section><h2>Limitations</h2>{}</section></article></main></body></html>'.format(
            html.escape(brief["title"]), html.escape(brief["title"]), html.escape(brief["summary"]), "".join(sections),
            "".join(f"<p>{html.escape(x)}</p>" for x in brief["methodology"]), "".join(f"<p>{html.escape(x)}</p>" for x in brief["limitations"]),
        )
        csv_io = io.StringIO(); writer = csv.writer(csv_io); writer.writerow(["evidence_id", "title", "source_id", "country", "indicator_id", "value", "unit", "observed_at", "truth_state", "record_sha256"])
        for e in brief["frozen_manifest"]["evidence"]:
            writer.writerow([e.get(k, "") for k in ["evidence_id", "title", "source_id", "country", "indicator_id", "value", "unit", "observed_at", "truth_state", "record_sha256"]])
        packet = {
            "schema": "sc-site-intelligence-publication-package/1.0", "version": APP_VERSION,
            "brief": brief, "accessibility": access,
            "formats": list(self.policy["export_formats"]), "generated_at": _now(),
            "print_html_ready": True, "accessible_pdf_source_ready": access["status"] == "pass",
            "pdf_binary_generated": False, "human_review_required": True,
            "automatic_publication": False, "write_performed": False,
        }
        packet["package_sha256"] = _digest({k: v for k, v in packet.items() if k != "package_sha256"})
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA, "contract": "publication-package", "packet": packet, "markdown": "\n".join(md), "print_html": print_html, "csv_evidence": csv_io.getvalue()}


_STUDIO = BriefingPublicationStudio()

def public_briefing_publication_studio() -> dict[str, Any]: return _STUDIO.schema()
def public_frozen_evidence_manifest(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _STUDIO.freeze_manifest(request)
def public_briefing_preview(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _STUDIO.briefing(request)
def public_story_map_preview(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _STUDIO.story_map(request)
def public_publication_readiness(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _STUDIO.readiness(request)
def public_publication_correction_preview(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _STUDIO.correction(request)
def public_publication_package(request: Mapping[str, Any] | None = None) -> dict[str, Any]: return _STUDIO.package(request)
