from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import html
import io
import json
import re
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from .config import Settings

RELEASE_VERSION = "3.17.0"
SCHEMA_VERSION = "sc-site-intelligence-publication-studio/1.0"
PROJECT_SCHEMA = "sc-site-intelligence-publication-project/1.0"
BLOCK_SCHEMA = "sc-site-intelligence-publication-block/1.0"
REVIEW_SCHEMA = "sc-site-intelligence-publication-review/1.0"
VERSION_SCHEMA = "sc-site-intelligence-publication-version/1.0"
EXPORT_SCHEMA = "sc-site-intelligence-publication-export/1.0"
PROJECT_STATUS = {"draft", "review", "approved", "published", "archived"}
VISIBILITY = {"private", "unlisted", "public"}
BLOCK_TYPES = {
    "narrative", "heading", "callout", "quote", "map", "timeline", "chart",
    "evidence_table", "source_list", "methodology", "image", "divider"
}
REVIEW_DECISIONS = {"approved", "changes_requested", "rejected"}
_SECRET = re.compile(r"(?:token|secret|password|authorization|api[_-]?key|email|phone|user[_-]?id)", re.I)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else Path(__file__).resolve().parents[2] / path


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _safe_id(value: str, fallback: str = "record") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.:-]+", "-", str(value or "").strip()).strip("-.:")
    return (cleaned or fallback)[:180]


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
    return (cleaned or "publication")[:140]


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


def _write_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def _read_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except (FileNotFoundError, OSError):
        return []
    rows = []
    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _clean_list(value: Any, maximum: int = 200, length: int = 500) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v).strip()[:length] for v in value[:maximum] if str(v).strip()]


class IntelligencePublishingStudio:
    def __init__(self, settings: Settings, now_fn: Callable[[], datetime] = _utc_now) -> None:
        self.settings = settings
        self.now_fn = now_fn
        self.projects_path = _resolve(settings.intelligence_publishing_projects_path)
        self.blocks_path = _resolve(settings.intelligence_publishing_blocks_path)
        self.reviews_path = _resolve(settings.intelligence_publishing_reviews_path)
        self.versions_path = _resolve(settings.intelligence_publishing_versions_path)
        self.policy = _read_json(_resolve(settings.intelligence_publishing_policy_path), {})
        self.max_records = settings.intelligence_publishing_max_records
        self.max_blocks = settings.intelligence_publishing_max_blocks
        self.max_block_chars = settings.intelligence_publishing_max_block_chars

    def _latest(self, path: Path, key: str) -> list[dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for item in _read_jsonl(path, self.max_records):
            if item.get(key):
                latest[str(item[key])] = item
        return list(latest.values())

    def _projects(self) -> list[dict[str, Any]]:
        return sorted(self._latest(self.projects_path, "project_id"), key=lambda x: str(x.get("updated_at", "")), reverse=True)

    def _project(self, project_id: str) -> dict[str, Any]:
        project_id = _safe_id(project_id)
        for item in self._projects():
            if item.get("project_id") == project_id:
                return item
        raise KeyError(project_id)

    def _blocks(self, project_id: str) -> list[dict[str, Any]]:
        project_id = _safe_id(project_id)
        rows = [x for x in self._latest(self.blocks_path, "block_id") if x.get("project_id") == project_id and not x.get("deleted")]
        return sorted(rows, key=lambda x: (int(x.get("position", 0)), str(x.get("block_id"))))

    def _reviews(self, project_id: str) -> list[dict[str, Any]]:
        return [x for x in _read_jsonl(self.reviews_path, self.max_records) if x.get("project_id") == _safe_id(project_id)]

    def _versions(self, project_id: str) -> list[dict[str, Any]]:
        return [x for x in _read_jsonl(self.versions_path, self.max_records) if x.get("project_id") == _safe_id(project_id)]

    def create_project(self, request: dict[str, Any]) -> dict[str, Any]:
        title = str(request.get("title") or "").strip()
        if not title:
            raise ValueError("title is required.")
        project_id = _safe_id(str(request.get("project_id") or f"publication:{uuid4().hex[:16]}"))
        previous = None
        try:
            previous = self._project(project_id)
        except KeyError:
            pass
        status = str(request.get("status") or (previous or {}).get("status") or "draft").lower()
        visibility = str(request.get("visibility") or (previous or {}).get("visibility") or "private").lower()
        if status not in PROJECT_STATUS or visibility not in VISIBILITY:
            raise ValueError("Unsupported publication status or visibility.")
        if status == "published" and not bool(request.get("_publish_transition")):
            raise ValueError("Use publish_project after human editorial approval.")
        now = self.now_fn()
        record = {
            "schema": PROJECT_SCHEMA,
            "release_version": RELEASE_VERSION,
            "project_id": project_id,
            "slug": _slug(str(request.get("slug") or title)),
            "title": title[:500],
            "subtitle": str(request.get("subtitle") or "")[:1000],
            "summary": str(request.get("summary") or "")[:5000],
            "publication_type": str(request.get("publication_type") or "intelligence-brief")[:100],
            "status": status,
            "visibility": visibility,
            "authors": _clean_list(request.get("authors"), 50, 300),
            "editors": _clean_list(request.get("editors"), 50, 300),
            "topics": _clean_list(request.get("topics"), 100, 200),
            "geographies": _clean_list(request.get("geographies"), 100, 200),
            "source_ids": _clean_list(request.get("source_ids"), 500, 300),
            "evidence_ids": _clean_list(request.get("evidence_ids"), 500, 300),
            "methodology_notes": _clean_list(request.get("methodology_notes"), 100, 2000),
            "limitations": _clean_list(request.get("limitations"), 100, 2000),
            "metadata": _redact(request.get("metadata") or {}),
            "created_at": previous.get("created_at") if previous else _iso(now),
            "updated_at": _iso(now),
            "supersedes_sha256": previous.get("project_sha256") if previous else "",
        }
        record["project_sha256"] = _digest({k: v for k, v in record.items() if k != "project_sha256"})
        _write_jsonl(self.projects_path, record)
        return {"ok": True, "project": record}

    def add_block(self, project_id: str, request: dict[str, Any]) -> dict[str, Any]:
        project = self._project(project_id)
        block_type = str(request.get("block_type") or "narrative").lower()
        if block_type not in BLOCK_TYPES:
            raise ValueError("Unsupported publication block type.")
        existing = self._blocks(project_id)
        if len(existing) >= self.max_blocks:
            raise ValueError("Publication block limit reached.")
        content = request.get("content") if isinstance(request.get("content"), dict) else {"text": str(request.get("content") or "")}
        if len(json.dumps(content, ensure_ascii=False)) > self.max_block_chars:
            raise ValueError("Publication block exceeds the configured size limit.")
        if block_type in {"map", "chart", "evidence_table", "source_list"} and not (_clean_list(request.get("source_ids"), 200, 300) or _clean_list(request.get("evidence_ids"), 200, 300)):
            raise ValueError(f"{block_type} blocks require source_ids or evidence_ids.")
        block_id = _safe_id(str(request.get("block_id") or f"block:{uuid4().hex[:16]}"))
        previous = next((x for x in existing if x.get("block_id") == block_id), None)
        record = {
            "schema": BLOCK_SCHEMA,
            "release_version": RELEASE_VERSION,
            "block_id": block_id,
            "project_id": project["project_id"],
            "block_type": block_type,
            "position": int(request.get("position", previous.get("position", len(existing) + 1) if previous else len(existing) + 1)),
            "title": str(request.get("title") or "")[:500],
            "content": _redact(content),
            "source_ids": _clean_list(request.get("source_ids"), 200, 300),
            "evidence_ids": _clean_list(request.get("evidence_ids"), 200, 300),
            "caption": str(request.get("caption") or "")[:2000],
            "alt_text": str(request.get("alt_text") or "")[:1000],
            "created_at": previous.get("created_at") if previous else _iso(self.now_fn()),
            "updated_at": _iso(self.now_fn()),
            "supersedes_sha256": previous.get("block_sha256") if previous else "",
        }
        record["block_sha256"] = _digest({k: v for k, v in record.items() if k != "block_sha256"})
        _write_jsonl(self.blocks_path, record)
        return {"ok": True, "block": record}

    def submit_review(self, project_id: str, request: dict[str, Any] | None = None) -> dict[str, Any]:
        request = request or {}
        project = self._project(project_id)
        if not self._blocks(project_id):
            raise ValueError("A publication requires at least one block before review.")
        updated = self.create_project({**project, "status": "review"})["project"]
        record = {
            "schema": REVIEW_SCHEMA,
            "release_version": RELEASE_VERSION,
            "review_id": _safe_id(str(request.get("review_id") or f"review:{uuid4().hex[:16]}")),
            "project_id": project["project_id"],
            "decision": "pending",
            "reviewer_role": str(request.get("reviewer_role") or "editor")[:200],
            "notes": str(request.get("notes") or "")[:5000],
            "submitted_at": _iso(self.now_fn()),
            "project_sha256": updated["project_sha256"],
        }
        record["review_sha256"] = _digest({k: v for k, v in record.items() if k != "review_sha256"})
        _write_jsonl(self.reviews_path, record)
        return {"ok": True, "review": record, "project": updated}

    def decide_review(self, project_id: str, request: dict[str, Any]) -> dict[str, Any]:
        project = self._project(project_id)
        decision = str(request.get("decision") or "").lower()
        if decision not in REVIEW_DECISIONS:
            raise ValueError("Unsupported review decision.")
        if not bool(request.get("human_review_confirmed")):
            raise ValueError("human_review_confirmed=true is required.")
        next_status = "approved" if decision == "approved" else "draft"
        updated = self.create_project({**project, "status": next_status})["project"]
        record = {
            "schema": REVIEW_SCHEMA,
            "release_version": RELEASE_VERSION,
            "review_id": _safe_id(str(request.get("review_id") or f"review:{uuid4().hex[:16]}")),
            "project_id": project["project_id"],
            "decision": decision,
            "reviewer_role": str(request.get("reviewer_role") or "editor")[:200],
            "reviewer_name": str(request.get("reviewer_name") or "")[:300],
            "notes": str(request.get("notes") or "")[:5000],
            "human_review_confirmed": True,
            "decided_at": _iso(self.now_fn()),
            "project_sha256": updated["project_sha256"],
        }
        record["review_sha256"] = _digest({k: v for k, v in record.items() if k != "review_sha256"})
        _write_jsonl(self.reviews_path, record)
        return {"ok": True, "review": record, "project": updated}

    def publish_project(self, project_id: str, request: dict[str, Any] | None = None) -> dict[str, Any]:
        request = request or {}
        project = self._project(project_id)
        if project.get("status") != "approved":
            raise ValueError("Publication requires an approved human editorial review.")
        if not bool(request.get("human_publish_confirmed")):
            raise ValueError("human_publish_confirmed=true is required.")
        blocks = self._blocks(project_id)
        if not blocks:
            raise ValueError("Publication requires at least one block.")
        visibility = str(request.get("visibility") or project.get("visibility") or "public").lower()
        if visibility not in {"public", "unlisted"}:
            raise ValueError("Published output must be public or unlisted.")
        previous_versions = self._versions(project_id)
        number = len(previous_versions) + 1
        published_project = self.create_project({**project, "status": "published", "visibility": visibility, "_publish_transition": True})["project"]
        snapshot = {
            "project": published_project,
            "blocks": blocks,
            "source_ids": sorted(set(published_project.get("source_ids", []) + [v for b in blocks for v in b.get("source_ids", [])])),
            "evidence_ids": sorted(set(published_project.get("evidence_ids", []) + [v for b in blocks for v in b.get("evidence_ids", [])])),
        }
        record = {
            "schema": VERSION_SCHEMA,
            "release_version": RELEASE_VERSION,
            "publication_id": published_project["project_id"],
            "project_id": published_project["project_id"],
            "version_number": number,
            "version_id": f"{published_project['project_id']}:v{number}",
            "visibility": visibility,
            "published_at": _iso(self.now_fn()),
            "editorial_approval": True,
            "snapshot": snapshot,
            "previous_version_sha256": previous_versions[-1].get("version_sha256") if previous_versions else "",
        }
        record["version_sha256"] = _digest({k: v for k, v in record.items() if k != "version_sha256"})
        _write_jsonl(self.versions_path, record)
        return {"ok": True, "publication": self._public_version(record), "immutable_version": record}

    def _public_version(self, record: dict[str, Any]) -> dict[str, Any]:
        snapshot = record.get("snapshot") or {}
        project = snapshot.get("project") or {}
        return {
            "schema": VERSION_SCHEMA,
            "release_version": RELEASE_VERSION,
            "publication_id": record.get("publication_id"),
            "version_id": record.get("version_id"),
            "version_number": record.get("version_number"),
            "version_sha256": record.get("version_sha256"),
            "published_at": record.get("published_at"),
            "visibility": record.get("visibility"),
            "title": project.get("title"),
            "subtitle": project.get("subtitle"),
            "summary": project.get("summary"),
            "slug": project.get("slug"),
            "publication_type": project.get("publication_type"),
            "authors": project.get("authors", []),
            "topics": project.get("topics", []),
            "geographies": project.get("geographies", []),
            "methodology_notes": project.get("methodology_notes", []),
            "limitations": project.get("limitations", []),
            "blocks": snapshot.get("blocks", []),
            "source_ids": snapshot.get("source_ids", []),
            "evidence_ids": snapshot.get("evidence_ids", []),
            "editorial_approval": True,
        }

    def public_publications(self, limit: int = 100) -> dict[str, Any]:
        latest: dict[str, dict[str, Any]] = {}
        for version in _read_jsonl(self.versions_path, self.max_records):
            if version.get("visibility") == "public":
                latest[str(version.get("publication_id"))] = version
        rows = [self._public_version(v) for v in latest.values()]
        rows.sort(key=lambda x: str(x.get("published_at", "")), reverse=True)
        return {"schema": SCHEMA_VERSION, "release_version": RELEASE_VERSION, "count": len(rows[:limit]), "publications": rows[:limit], "unlisted_omitted": True}

    def publication_detail(self, publication_id: str, public: bool = True) -> dict[str, Any]:
        versions = self._versions(publication_id)
        if not versions:
            raise KeyError(publication_id)
        record = versions[-1]
        if public and record.get("visibility") not in {"public", "unlisted"}:
            raise KeyError(publication_id)
        return self._public_version(record) if public else record

    def version_history(self, publication_id: str, public: bool = True) -> dict[str, Any]:
        versions = self._versions(publication_id)
        if public:
            versions = [v for v in versions if v.get("visibility") in {"public", "unlisted"}]
        if not versions:
            raise KeyError(publication_id)
        return {"schema": VERSION_SCHEMA, "release_version": RELEASE_VERSION, "publication_id": _safe_id(publication_id), "count": len(versions), "versions": [{k: v.get(k) for k in ["version_id", "version_number", "version_sha256", "published_at", "visibility"]} for v in versions]}

    def story_map(self, publication_id: str, public: bool = True) -> dict[str, Any]:
        item = self.publication_detail(publication_id, public=public)
        blocks = [b for b in item.get("blocks", []) if b.get("block_type") in {"map", "timeline", "narrative", "heading", "callout", "image"}]
        return {
            "schema": "sc-site-intelligence-story-map/1.0",
            "release_version": RELEASE_VERSION,
            "publication_id": item["publication_id"],
            "title": item["title"],
            "blocks": blocks,
            "map_block_count": sum(1 for b in blocks if b.get("block_type") == "map"),
            "timeline_block_count": sum(1 for b in blocks if b.get("block_type") == "timeline"),
            "source_ids": item.get("source_ids", []),
            "evidence_ids": item.get("evidence_ids", []),
            "interpretation_boundary": "Story sequence, map proximity, and temporal adjacency do not establish causation.",
        }

    def export_publication(self, publication_id: str, public: bool = True) -> dict[str, Any]:
        item = self.publication_detail(publication_id, public=public)
        markdown = [f"# {item.get('title')}"]
        if item.get("subtitle"):
            markdown.append(f"\n_{item['subtitle']}_")
        if item.get("summary"):
            markdown.append(f"\n{item['summary']}")
        for block in item.get("blocks", []):
            title = block.get("title")
            if title:
                markdown.append(f"\n## {title}")
            content = block.get("content") or {}
            text = content.get("text") if isinstance(content, dict) else str(content)
            if text:
                markdown.append(f"\n{text}")
            refs = block.get("source_ids", []) + block.get("evidence_ids", [])
            if refs:
                markdown.append("\nReferences: " + ", ".join(refs))
        markdown.append("\n## Methodology and limitations")
        markdown.extend([f"- {x}" for x in item.get("methodology_notes", []) + item.get("limitations", [])])
        body = "\n".join(markdown)
        html_body = "<article><h1>{}</h1><p>{}</p>{}</article>".format(
            html.escape(str(item.get("title") or "")),
            html.escape(str(item.get("summary") or "")),
            "".join(f"<section><h2>{html.escape(str(b.get('title') or b.get('block_type')))}</h2><p>{html.escape(str((b.get('content') or {}).get('text') or ''))}</p></section>" for b in item.get("blocks", [])),
        )
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["position", "block_type", "title", "text", "source_ids", "evidence_ids"])
        for block in item.get("blocks", []):
            writer.writerow([block.get("position"), block.get("block_type"), block.get("title"), (block.get("content") or {}).get("text", ""), "|".join(block.get("source_ids", [])), "|".join(block.get("evidence_ids", []))])
        packet = {
            "schema": EXPORT_SCHEMA,
            "release_version": RELEASE_VERSION,
            "publication": item,
            "formats": ["json", "csv", "markdown", "print-html"],
            "generated_at": _iso(self.now_fn()),
            "pdf_ready_html": True,
            "pdf_binary_generated": False,
        }
        packet["packet_sha256"] = _digest({k: v for k, v in packet.items() if k != "packet_sha256"})
        return {"ok": True, "packet": packet, "json": packet, "csv": output.getvalue(), "markdown": body, "html": html_body}

    def wordpress_handoff(self, publication_id: str) -> dict[str, Any]:
        item = self.publication_detail(publication_id, public=False)
        return {
            "schema": "sc-site-intelligence-wordpress-publication-handoff/1.0",
            "release_version": RELEASE_VERSION,
            "destination": "wordpress",
            "read_only": True,
            "write_performed": False,
            "publication": self._public_version(item),
            "suggested_shortcode": f'[sc_intelligence_publication publication_id="{_safe_id(publication_id)}"]',
        }

    def diagnostics(self, public: bool = False) -> dict[str, Any]:
        projects = self._projects()
        versions = _read_jsonl(self.versions_path, self.max_records)
        blocks = self._latest(self.blocks_path, "block_id")
        reviews = _read_jsonl(self.reviews_path, self.max_records)
        public_versions = [v for v in versions if v.get("visibility") == "public"]
        return {
            "schema": SCHEMA_VERSION,
            "release_version": RELEASE_VERSION,
            "counts": {
                "projects": len(projects), "blocks": len(blocks), "reviews": len(reviews), "versions": len(versions), "publications": len({v.get('publication_id') for v in public_versions}),
                "story_map_blocks": sum(1 for b in blocks if b.get("block_type") in {"map", "timeline"}),
            },
            "project_statuses": dict(Counter(str(p.get("status")) for p in projects)),
            "block_types": dict(Counter(str(b.get("block_type")) for b in blocks)),
            "human_editorial_approval_required": True,
            "automatic_publication": False,
            "unlisted_omitted_from_directory": True,
            "public": public,
        }

    def public_summary(self) -> dict[str, Any]:
        data = self.public_publications(limit=100)
        diag = self.diagnostics(public=True)
        return {
            "schema": SCHEMA_VERSION,
            "release_version": RELEASE_VERSION,
            "title": "Intelligence Publishing and Story Map Studio",
            "description": "Human-reviewed intelligence publications composed from narrative, map, timeline, chart, evidence, source, and methodology blocks.",
            "counts": diag["counts"],
            "publication_types": sorted(set(x.get("publication_type", "intelligence-brief") for x in data["publications"])),
            "formats": ["json", "csv", "markdown", "print-html"],
            "boundaries": self.policy.get("boundaries", []),
            "human_editorial_approval_required": True,
            "automatic_publication": False,
        }

    def methodology(self) -> dict[str, Any]:
        return {"schema": SCHEMA_VERSION, "release_version": RELEASE_VERSION, "policy": self.policy, "block_types": sorted(BLOCK_TYPES), "publication_workflow": ["draft", "review", "approved", "published", "archived"]}

    def control_center(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "release_version": RELEASE_VERSION,
            "counts": self.diagnostics()["counts"],
            "projects": self._projects()[-100:],
            "recent_reviews": _read_jsonl(self.reviews_path, 100),
            "recent_versions": _read_jsonl(self.versions_path, 100),
            "policy": self.policy,
        }
