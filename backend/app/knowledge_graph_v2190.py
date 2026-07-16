from __future__ import annotations

from collections import Counter, deque
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from .config import Settings

RELEASE_VERSION = "2.20.0"
SCHEMA_VERSION = "sc-site-intelligence-knowledge-graph/1.0"
ENTITY_SCHEMA = "sc-site-intelligence-graph-entity/1.0"
RELATIONSHIP_SCHEMA = "sc-site-intelligence-graph-relationship/1.0"
ALIAS_SCHEMA = "sc-site-intelligence-graph-alias/1.0"
EXPORT_SCHEMA = "sc-site-intelligence-graph-export/1.0"
VISIBILITY = {"public", "private"}
ENTITY_STATUS = {"draft", "review", "approved", "retired", "superseded"}
RELATIONSHIP_STATUS = {"draft", "review", "approved", "rejected", "superseded"}
CONFIDENCE_LABELS = {"unknown", "low", "moderate", "high", "verified"}
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


def _normalize_alias(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


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
    rows: list[dict[str, Any]] = []
    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): ("[redacted]" if _SECRET.search(str(k)) else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _clean_list(values: Any, maximum: int = 100, length: int = 240) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip()[:length] for item in values[:maximum] if str(item).strip()]


def _parse_date(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid ISO date/time: {text}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class KnowledgeGraphExplorer:
    def __init__(self, settings: Settings, now_fn: Callable[[], datetime] = _utc_now) -> None:
        self.settings = settings
        self.now_fn = now_fn
        self.entities_path = _resolve(settings.knowledge_graph_entities_path)
        self.relationships_path = _resolve(settings.knowledge_graph_relationships_path)
        self.aliases_path = _resolve(settings.knowledge_graph_aliases_path)
        self.policy = _read_json(_resolve(settings.knowledge_graph_policy_path), {})
        self.registry = _read_json(_resolve(settings.knowledge_graph_relationship_registry_path), {})
        self.max_records = settings.knowledge_graph_max_records
        self.max_depth = settings.knowledge_graph_max_traversal_depth
        self.max_results = settings.knowledge_graph_max_results
        self.entity_types = set(self.registry.get("entity_types", []))
        self.relationship_types = {
            str(item.get("id")): item
            for item in self.registry.get("relationship_types", [])
            if isinstance(item, dict) and item.get("id")
        }

    def _rows(self, path: Path) -> list[dict[str, Any]]:
        return _read_jsonl(path, self.max_records)

    def _latest(self, rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for item in rows:
            if item.get(key):
                latest[str(item[key])] = item
        return list(latest.values())

    def _entities(self, public: bool = False) -> list[dict[str, Any]]:
        rows = self._latest(self._rows(self.entities_path), "entity_id")
        if public:
            rows = [r for r in rows if r.get("visibility") == "public" and r.get("status") == "approved"]
        return sorted(rows, key=lambda r: (str(r.get("entity_type")), str(r.get("label")), str(r.get("entity_id"))))

    def _relationships(self, public: bool = False, as_of: str = "") -> list[dict[str, Any]]:
        rows = self._latest(self._rows(self.relationships_path), "relationship_id")
        if public:
            rows = [r for r in rows if r.get("visibility") == "public" and r.get("status") == "approved"]
        if as_of:
            at = _parse_date(as_of)
            assert at is not None
            filtered = []
            for item in rows:
                start = _parse_date(item.get("valid_from"))
                end = _parse_date(item.get("valid_to"))
                if start and at < start:
                    continue
                if end and at > end:
                    continue
                filtered.append(item)
            rows = filtered
        return sorted(rows, key=lambda r: (str(r.get("relationship_type")), str(r.get("relationship_id"))))

    def _entity(self, entity_id: str, public: bool = False) -> dict[str, Any]:
        entity_id = _safe_id(entity_id)
        rows = [r for r in self._entities(public=public) if r.get("entity_id") == entity_id]
        if not rows:
            raise KeyError(entity_id)
        return rows[-1]

    def _relationship(self, relationship_id: str, public: bool = False) -> dict[str, Any]:
        relationship_id = _safe_id(relationship_id)
        rows = [r for r in self._relationships(public=public) if r.get("relationship_id") == relationship_id]
        if not rows:
            raise KeyError(relationship_id)
        return rows[-1]

    def register_entity(self, request: dict[str, Any]) -> dict[str, Any]:
        raw_id = str(request.get("entity_id") or "").strip()
        label = str(request.get("label") or "").strip()
        entity_type = str(request.get("entity_type") or "").strip().lower()
        status = str(request.get("status") or "draft").strip().lower()
        visibility = str(request.get("visibility") or "private").strip().lower()
        if not raw_id or not label or entity_type not in self.entity_types:
            raise ValueError("entity_id, label, and a registered entity_type are required.")
        if status not in ENTITY_STATUS or visibility not in VISIBILITY:
            raise ValueError("Unsupported entity status or visibility.")
        if visibility == "public" and status == "approved" and not bool(request.get("human_review_confirmed")):
            raise ValueError("Public approved entities require human_review_confirmed=true.")
        entity_id = _safe_id(raw_id)
        now = self.now_fn()
        previous = None
        try:
            previous = self._entity(entity_id)
        except KeyError:
            pass
        identifiers = request.get("identifiers") if isinstance(request.get("identifiers"), dict) else {}
        aliases = _clean_list(request.get("aliases"), 100, 300)
        record = {
            "schema": ENTITY_SCHEMA,
            "release_version": RELEASE_VERSION,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "label": label[:500],
            "description": str(request.get("description") or "")[:4000],
            "status": status,
            "visibility": visibility,
            "aliases": aliases,
            "identifiers": {str(k)[:100]: str(v)[:500] for k, v in identifiers.items() if str(k).strip() and str(v).strip()},
            "canonical_url": str(request.get("canonical_url") or "")[:2000],
            "source_system": str(request.get("source_system") or "manual")[:200],
            "source_record_id": str(request.get("source_record_id") or "")[:500],
            "metadata": _redact(request.get("metadata") or {}),
            "human_review_confirmed": bool(request.get("human_review_confirmed")),
            "created_at": previous.get("created_at") if previous else _iso(now),
            "updated_at": _iso(now),
            "supersedes_sha256": previous.get("entity_sha256") if previous else "",
        }
        record["entity_sha256"] = _digest({k: v for k, v in record.items() if k != "entity_sha256"})
        _write_jsonl(self.entities_path, record)
        for alias in aliases:
            self.register_alias({"entity_id": entity_id, "alias": alias, "namespace": "label", "visibility": visibility})
        for namespace, value in record["identifiers"].items():
            self.register_alias({"entity_id": entity_id, "alias": value, "namespace": namespace, "visibility": visibility})
        return {"ok": True, "entity": record}

    def register_alias(self, request: dict[str, Any]) -> dict[str, Any]:
        entity_id = _safe_id(str(request.get("entity_id") or ""))
        self._entity(entity_id)
        alias = str(request.get("alias") or "").strip()
        namespace = _safe_id(str(request.get("namespace") or "label"), "label")
        visibility = str(request.get("visibility") or "private").strip().lower()
        if not alias or visibility not in VISIBILITY:
            raise ValueError("alias and a supported visibility are required.")
        normalized = _normalize_alias(alias)
        if not normalized:
            raise ValueError("Alias cannot normalize to an empty value.")
        record = {
            "schema": ALIAS_SCHEMA,
            "release_version": RELEASE_VERSION,
            "alias_id": _safe_id(str(request.get("alias_id") or f"{namespace}:{normalized}:{entity_id}")),
            "entity_id": entity_id,
            "namespace": namespace,
            "alias": alias[:500],
            "normalized_alias": normalized[:500],
            "visibility": visibility,
            "registered_at": _iso(self.now_fn()),
        }
        record["alias_sha256"] = _digest({k: v for k, v in record.items() if k != "alias_sha256"})
        _write_jsonl(self.aliases_path, record)
        return {"ok": True, "alias": record}

    def register_relationship(self, request: dict[str, Any]) -> dict[str, Any]:
        source_id = _safe_id(str(request.get("source_entity_id") or ""))
        target_id = _safe_id(str(request.get("target_entity_id") or ""))
        relationship_type = str(request.get("relationship_type") or "").strip().lower()
        relation_policy = self.relationship_types.get(relationship_type)
        if not source_id or not target_id or not relation_policy:
            raise ValueError("source_entity_id, target_entity_id, and a registered relationship_type are required.")
        if source_id == target_id and not bool(relation_policy.get("self_relationship_allowed")):
            raise ValueError("This relationship type does not permit self-relationships.")
        source = self._entity(source_id)
        target = self._entity(target_id)
        visibility = str(request.get("visibility") or "private").strip().lower()
        status = str(request.get("status") or "draft").strip().lower()
        if visibility not in VISIBILITY or status not in RELATIONSHIP_STATUS:
            raise ValueError("Unsupported relationship status or visibility.")
        evidence_ids = _clean_list(request.get("evidence_ids"), 200, 240)
        source_ids = _clean_list(request.get("source_ids"), 200, 500)
        if relation_policy.get("evidence_required", True) and not (evidence_ids or source_ids):
            raise ValueError("This relationship type requires evidence_ids or source_ids.")
        if visibility == "public":
            if source.get("visibility") != "public" or target.get("visibility") != "public":
                raise ValueError("Public relationships require public source and target entities.")
            if status == "approved" and not bool(request.get("human_review_confirmed")):
                raise ValueError("Public approved relationships require human_review_confirmed=true.")
        valid_from = str(request.get("valid_from") or "").strip()
        valid_to = str(request.get("valid_to") or "").strip()
        start = _parse_date(valid_from)
        end = _parse_date(valid_to)
        if start and end and end < start:
            raise ValueError("valid_to cannot be earlier than valid_from.")
        confidence = str(request.get("confidence") or "unknown").strip().lower()
        if confidence not in CONFIDENCE_LABELS:
            raise ValueError("Unsupported confidence label.")
        raw_score = request.get("confidence_score")
        score = None if raw_score in (None, "") else float(raw_score)
        if score is not None and not 0 <= score <= 1:
            raise ValueError("confidence_score must be between 0 and 1.")
        relationship_id = _safe_id(str(request.get("relationship_id") or uuid4()))
        now = self.now_fn()
        previous = None
        try:
            previous = self._relationship(relationship_id)
        except KeyError:
            pass
        record = {
            "schema": RELATIONSHIP_SCHEMA,
            "release_version": RELEASE_VERSION,
            "relationship_id": relationship_id,
            "relationship_type": relationship_type,
            "label": str(request.get("label") or relation_policy.get("label") or relationship_type.replace("_", " "))[:500],
            "source_entity_id": source_id,
            "target_entity_id": target_id,
            "directed": bool(relation_policy.get("directed", True)),
            "inverse_relationship_type": str(relation_policy.get("inverse") or "")[:120],
            "status": status,
            "visibility": visibility,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "observed_at": str(request.get("observed_at") or "")[:120],
            "evidence_ids": evidence_ids,
            "source_ids": source_ids,
            "confidence": confidence,
            "confidence_score": score,
            "confidence_basis": str(request.get("confidence_basis") or "")[:2000],
            "causal_claim": bool(relation_policy.get("causal", False)),
            "causation_not_inferred": not bool(relation_policy.get("causal", False)),
            "metadata": _redact(request.get("metadata") or {}),
            "human_review_confirmed": bool(request.get("human_review_confirmed")),
            "created_at": previous.get("created_at") if previous else _iso(now),
            "updated_at": _iso(now),
            "supersedes_sha256": previous.get("relationship_sha256") if previous else "",
        }
        record["relationship_sha256"] = _digest({k: v for k, v in record.items() if k != "relationship_sha256"})
        _write_jsonl(self.relationships_path, record)
        return {"ok": True, "relationship": record}

    def resolve(self, query: str, public: bool = False, namespace: str = "") -> dict[str, Any]:
        normalized = _normalize_alias(query)
        entities = {e["entity_id"]: e for e in self._entities(public=public)}
        matches: list[dict[str, Any]] = []
        for entity in entities.values():
            haystacks = [entity.get("entity_id", ""), entity.get("label", ""), *entity.get("aliases", [])]
            if any(_normalize_alias(v) == normalized for v in haystacks):
                matches.append({"entity": entity, "match_type": "entity", "namespace": "canonical"})
        aliases = self._latest(self._rows(self.aliases_path), "alias_id")
        for alias in aliases:
            if public and alias.get("visibility") != "public":
                continue
            if namespace and alias.get("namespace") != namespace:
                continue
            if alias.get("normalized_alias") == normalized and alias.get("entity_id") in entities:
                matches.append({"entity": entities[alias["entity_id"]], "match_type": "alias", "namespace": alias.get("namespace"), "alias": alias.get("alias")})
        unique: dict[str, dict[str, Any]] = {}
        for item in matches:
            unique[item["entity"]["entity_id"]] = item
        rows = list(unique.values())[: self.max_results]
        return {"schema": SCHEMA_VERSION, "release_version": RELEASE_VERSION, "query": query, "normalized_query": normalized, "count": len(rows), "matches": rows, "ambiguous": len(rows) > 1, "automatic_merge": False}

    def preview_reconciliation(self, request: dict[str, Any], public: bool = False) -> dict[str, Any]:
        queries = _clean_list(request.get("queries"), 50, 500)
        identifiers = request.get("identifiers") if isinstance(request.get("identifiers"), dict) else {}
        candidates: dict[str, dict[str, Any]] = {}
        for query in queries:
            for match in self.resolve(query, public=public).get("matches", []):
                entity = match["entity"]
                candidates[entity["entity_id"]] = {"entity": entity, "matched_by": sorted(set(candidates.get(entity["entity_id"], {}).get("matched_by", []) + [query]))}
        for namespace, value in identifiers.items():
            for match in self.resolve(str(value), public=public, namespace=str(namespace)).get("matches", []):
                entity = match["entity"]
                candidates[entity["entity_id"]] = {"entity": entity, "matched_by": sorted(set(candidates.get(entity["entity_id"], {}).get("matched_by", []) + [f"{namespace}:{value}"]))}
        rows = list(candidates.values())[: self.max_results]
        return {"schema": "sc-site-intelligence-entity-reconciliation-preview/1.0", "release_version": RELEASE_VERSION, "candidate_count": len(rows), "candidates": rows, "automatic_merge": False, "human_review_required": True}

    def entities(self, public: bool = False, entity_type: str = "", query: str = "", limit: int = 100) -> dict[str, Any]:
        rows = self._entities(public=public)
        if entity_type:
            rows = [r for r in rows if r.get("entity_type") == entity_type]
        if query:
            needle = _normalize_alias(query)
            rows = [r for r in rows if needle in _normalize_alias(" ".join([str(r.get("entity_id", "")), str(r.get("label", "")), " ".join(r.get("aliases", []))]))]
        rows = rows[: min(max(1, limit), self.max_results)]
        return {"schema": SCHEMA_VERSION, "release_version": RELEASE_VERSION, "count": len(rows), "entities": rows}

    def relationships(self, public: bool = False, relationship_type: str = "", entity_id: str = "", as_of: str = "", limit: int = 200) -> dict[str, Any]:
        rows = self._relationships(public=public, as_of=as_of)
        if relationship_type:
            rows = [r for r in rows if r.get("relationship_type") == relationship_type]
        if entity_id:
            entity_id = _safe_id(entity_id)
            rows = [r for r in rows if entity_id in {r.get("source_entity_id"), r.get("target_entity_id")}]
        rows = rows[: min(max(1, limit), self.max_results)]
        return {"schema": SCHEMA_VERSION, "release_version": RELEASE_VERSION, "count": len(rows), "relationships": rows}

    def entity_detail(self, entity_id: str, public: bool = False, as_of: str = "") -> dict[str, Any]:
        entity = self._entity(entity_id, public=public)
        relationships = [r for r in self._relationships(public=public, as_of=as_of) if entity["entity_id"] in {r.get("source_entity_id"), r.get("target_entity_id")}]
        entity_ids = {entity["entity_id"]}
        for relation in relationships:
            entity_ids.add(str(relation.get("source_entity_id")))
            entity_ids.add(str(relation.get("target_entity_id")))
        lookup = {e["entity_id"]: e for e in self._entities(public=public) if e["entity_id"] in entity_ids}
        aliases = [a for a in self._latest(self._rows(self.aliases_path), "alias_id") if a.get("entity_id") == entity["entity_id"] and (not public or a.get("visibility") == "public")]
        return {"schema": SCHEMA_VERSION, "release_version": RELEASE_VERSION, "entity": entity, "aliases": aliases, "relationships": relationships, "related_entities": list(lookup.values()), "relationship_count": len(relationships)}

    def traverse(self, entity_id: str, public: bool = False, depth: int = 2, direction: str = "both", relationship_types: list[str] | None = None, as_of: str = "") -> dict[str, Any]:
        start = self._entity(entity_id, public=public)
        depth = min(max(0, int(depth)), self.max_depth)
        if direction not in {"out", "in", "both"}:
            raise ValueError("direction must be out, in, or both.")
        allowed = set(relationship_types or [])
        relationships = self._relationships(public=public, as_of=as_of)
        if allowed:
            relationships = [r for r in relationships if r.get("relationship_type") in allowed]
        by_node: dict[str, list[tuple[dict[str, Any], str]]] = {}
        for rel in relationships:
            s, t = str(rel.get("source_entity_id")), str(rel.get("target_entity_id"))
            if direction in {"out", "both"}:
                by_node.setdefault(s, []).append((rel, t))
            if direction in {"in", "both"}:
                by_node.setdefault(t, []).append((rel, s))
            if not rel.get("directed"):
                by_node.setdefault(t, []).append((rel, s))
                by_node.setdefault(s, []).append((rel, t))
        visited = {start["entity_id"]: 0}
        queue: deque[str] = deque([start["entity_id"]])
        edge_map: dict[str, dict[str, Any]] = {}
        while queue and len(visited) < self.max_results:
            current = queue.popleft()
            current_depth = visited[current]
            if current_depth >= depth:
                continue
            for rel, neighbor in by_node.get(current, []):
                edge_map[str(rel["relationship_id"])] = rel
                if neighbor not in visited:
                    visited[neighbor] = current_depth + 1
                    queue.append(neighbor)
                if len(visited) >= self.max_results:
                    break
        entity_lookup = {e["entity_id"]: e for e in self._entities(public=public)}
        nodes = [{**entity_lookup[eid], "graph_depth": d} for eid, d in visited.items() if eid in entity_lookup]
        return {"schema": "sc-site-intelligence-graph-traversal/1.0", "release_version": RELEASE_VERSION, "start_entity_id": start["entity_id"], "requested_depth": depth, "direction": direction, "node_count": len(nodes), "edge_count": len(edge_map), "nodes": nodes, "relationships": list(edge_map.values()), "truncated": len(visited) >= self.max_results, "causation_not_inferred": True}

    def shortest_path(self, source_id: str, target_id: str, public: bool = False, max_depth: int = 4, relationship_types: list[str] | None = None, as_of: str = "") -> dict[str, Any]:
        source = self._entity(source_id, public=public)
        target = self._entity(target_id, public=public)
        max_depth = min(max(1, int(max_depth)), self.max_depth)
        allowed = set(relationship_types or [])
        relationships = self._relationships(public=public, as_of=as_of)
        if allowed:
            relationships = [r for r in relationships if r.get("relationship_type") in allowed]
        adjacency: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        for rel in relationships:
            s, t = str(rel.get("source_entity_id")), str(rel.get("target_entity_id"))
            # Relationship-explorer paths treat typed edges as navigable in both
            # directions while preserving the canonical source/target orientation.
            adjacency.setdefault(s, []).append((t, rel))
            adjacency.setdefault(t, []).append((s, rel))
        queue: deque[tuple[str, list[str], list[dict[str, Any]]]] = deque([(source["entity_id"], [source["entity_id"]], [])])
        seen = {source["entity_id"]}
        found_nodes: list[str] = []
        found_edges: list[dict[str, Any]] = []
        while queue:
            node, path_nodes, path_edges = queue.popleft()
            if node == target["entity_id"]:
                found_nodes, found_edges = path_nodes, path_edges
                break
            if len(path_edges) >= max_depth:
                continue
            for neighbor, rel in adjacency.get(node, []):
                if neighbor in seen:
                    continue
                seen.add(neighbor)
                queue.append((neighbor, path_nodes + [neighbor], path_edges + [rel]))
        lookup = {e["entity_id"]: e for e in self._entities(public=public)}
        return {"schema": "sc-site-intelligence-graph-path/1.0", "release_version": RELEASE_VERSION, "source_entity_id": source["entity_id"], "target_entity_id": target["entity_id"], "found": bool(found_nodes), "hop_count": len(found_edges), "entities": [lookup[eid] for eid in found_nodes if eid in lookup], "relationships": found_edges, "causation_not_inferred": True}

    def diagnostics(self, public: bool = False) -> dict[str, Any]:
        entities = self._entities(public=public)
        entity_ids = {e["entity_id"] for e in entities}
        relationships = self._relationships(public=public)
        aliases = self._latest(self._rows(self.aliases_path), "alias_id")
        if public:
            aliases = [a for a in aliases if a.get("visibility") == "public" and a.get("entity_id") in entity_ids]
        degree = Counter()
        dangling = []
        unbacked = []
        for rel in relationships:
            s, t = rel.get("source_entity_id"), rel.get("target_entity_id")
            if s not in entity_ids or t not in entity_ids:
                dangling.append(rel.get("relationship_id"))
            degree[str(s)] += 1
            degree[str(t)] += 1
            if not rel.get("evidence_ids") and not rel.get("source_ids"):
                unbacked.append(rel.get("relationship_id"))
        alias_targets: dict[tuple[str, str], set[str]] = {}
        for alias in aliases:
            alias_targets.setdefault((str(alias.get("namespace")), str(alias.get("normalized_alias"))), set()).add(str(alias.get("entity_id")))
        collisions = [{"namespace": k[0], "normalized_alias": k[1], "entity_ids": sorted(v)} for k, v in alias_targets.items() if len(v) > 1]
        orphans = [eid for eid in entity_ids if degree[eid] == 0]
        return {"schema": SCHEMA_VERSION, "release_version": RELEASE_VERSION, "ok": not dangling, "public": public, "counts": {"entities": len(entities), "relationships": len(relationships), "aliases": len(aliases), "orphans": len(orphans), "dangling_relationships": len(dangling), "unbacked_relationships": len(unbacked), "alias_collisions": len(collisions)}, "orphan_entity_ids": orphans[:100], "dangling_relationship_ids": dangling[:100], "unbacked_relationship_ids": unbacked[:100], "alias_collisions": collisions[:100], "automatic_merge": False, "causation_not_inferred": True}

    def public_summary(self) -> dict[str, Any]:
        entities = self._entities(public=True)
        relationships = self._relationships(public=True)
        return {"schema": SCHEMA_VERSION, "release_version": RELEASE_VERSION, "title": "Intelligence Publishing and Story Map Studio", "counts": {"entities": len(entities), "relationships": len(relationships), "entity_types": len(set(e.get("entity_type") for e in entities)), "relationship_types": len(set(r.get("relationship_type") for r in relationships))}, "entity_type_counts": dict(Counter(str(e.get("entity_type")) for e in entities)), "relationship_type_counts": dict(Counter(str(r.get("relationship_type")) for r in relationships)), "boundaries": list(self.policy.get("boundaries", [])), "evidence_backed_relationships": True, "automatic_causation": False, "automatic_entity_merge": False}

    def methodology(self) -> dict[str, Any]:
        return {"schema": SCHEMA_VERSION, "release_version": RELEASE_VERSION, "policy": self.policy, "registry": self.registry, "temporal_relationships": True, "evidence_backing_required": True}

    def control_center(self) -> dict[str, Any]:
        entities = self._entities()
        relationships = self._relationships()
        diagnostics = self.diagnostics()
        return {"schema": SCHEMA_VERSION, "release_version": RELEASE_VERSION, "counts": diagnostics["counts"], "entities": entities[-100:], "relationships": relationships[-100:], "diagnostics": diagnostics, "policy": self.policy, "registry": self.registry}

    def export_subgraph(self, entity_id: str, public: bool = False, depth: int = 2, as_of: str = "") -> dict[str, Any]:
        traversal = self.traverse(entity_id, public=public, depth=depth, as_of=as_of)
        packet = {"schema": EXPORT_SCHEMA, "release_version": RELEASE_VERSION, "generated_at": _iso(self.now_fn()), "read_only": True, "as_of": as_of, "nodes": traversal["nodes"], "relationships": traversal["relationships"], "governance": {"causation_not_inferred": True, "automatic_merge": False, "evidence_required": True}}
        packet["packet_sha256"] = _digest({k: v for k, v in packet.items() if k != "packet_sha256"})
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["relationship_id", "relationship_type", "source_entity_id", "target_entity_id", "confidence", "valid_from", "valid_to", "evidence_ids", "source_ids"])
        for rel in traversal["relationships"]:
            writer.writerow([rel.get("relationship_id"), rel.get("relationship_type"), rel.get("source_entity_id"), rel.get("target_entity_id"), rel.get("confidence"), rel.get("valid_from"), rel.get("valid_to"), "|".join(rel.get("evidence_ids", [])), "|".join(rel.get("source_ids", []))])
        return {"schema": EXPORT_SCHEMA, "release_version": RELEASE_VERSION, "read_only": True, "packet": packet, "csv": out.getvalue()}

    def platform_core_handoff(self, entity_id: str, depth: int = 2, public: bool = False) -> dict[str, Any]:
        export = self.export_subgraph(entity_id, public=public, depth=depth)
        return {"schema": "sc-site-intelligence-platform-core-graph-handoff/1.0", "release_version": RELEASE_VERSION, "destination": "platform-core", "read_only": True, "write_performed": False, "packet": export["packet"], "instructions": "Validate entity identifiers, relationship evidence, temporal bounds, visibility, and human-review status before importing. Do not infer causation or merge entities automatically."}
