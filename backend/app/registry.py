from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .models import ContentItem, Registry, RegistryMatch, RegistrySuggestion


SYSTEM_PATH_PATTERNS = (
    "/wp-admin/",
    "/wp-json/",
    "/wp-content/",
    "/xmlrpc.php",
    "/feed/",
    "/author/",
    "/tag/",
    "/category/uncategorized/",
)


INFERENCE_RULES = [
    {
        "id": "publications",
        "hub": "Publications",
        "article_map": "Publications",
        "discipline": "Publishing",
        "content_type": "hub",
        "patterns": ["/publications/", "publications"],
        "confidence": 0.92,
    },
    {
        "id": "research-library",
        "hub": "Research",
        "article_map": "Research Library",
        "discipline": "Knowledge Systems",
        "content_type": "hub",
        "patterns": ["/research-library/", "research library", "learning architecture"],
        "confidence": 0.90,
    },
    {
        "id": "platform",
        "hub": "Platform",
        "article_map": "Platform",
        "discipline": "Platform Infrastructure",
        "content_type": "platform",
        "patterns": ["/platform/", "platform demos", "site intelligence", "feature suggestions"],
        "confidence": 0.87,
    },
    {
        "id": "workbench",
        "hub": "Platform",
        "article_map": "Workbench",
        "discipline": "Modeling and Analytics",
        "content_type": "platform",
        "patterns": ["/workbench/", "workbench", "calculator", "scorecard", "scenario tool"],
        "confidence": 0.88,
    },
    {
        "id": "research-librarian",
        "hub": "Platform",
        "article_map": "Research Librarian",
        "discipline": "Knowledge Systems",
        "content_type": "platform",
        "patterns": ["/research-librarian", "research librarian", "librarian ai"],
        "confidence": 0.88,
    },
    {
        "id": "decision-studio",
        "hub": "Platform",
        "article_map": "Decision Studio",
        "discipline": "Decision Science",
        "content_type": "platform",
        "patterns": ["/decision-studio/", "decision studio"],
        "confidence": 0.88,
    },
    {
        "id": "mathematical-modeling",
        "hub": "Research",
        "article_map": "Mathematical Modeling",
        "discipline": "Mathematics",
        "content_type": "article_map",
        "patterns": ["/mathematical-modeling/", "mathematical modeling"],
        "confidence": 0.89,
    },
    {
        "id": "linear-algebra",
        "hub": "Research",
        "article_map": "Linear Algebra for Systems Modeling",
        "discipline": "Mathematics",
        "content_type": "article",
        "patterns": ["/linear-algebra", "linear algebra", "matrices", "eigenvalue", "markov"],
        "confidence": 0.90,
    },
    {
        "id": "calculus",
        "hub": "Research",
        "article_map": "Calculus for Systems Modeling",
        "discipline": "Mathematics",
        "content_type": "article",
        "patterns": ["/calculus", "calculus", "derivative", "integral", "limits"],
        "confidence": 0.90,
    },
    {
        "id": "probability-statistics",
        "hub": "Research",
        "article_map": "Probability and Statistics",
        "discipline": "Mathematics",
        "content_type": "article",
        "patterns": ["probability", "statistics", "statistical", "variance", "sampling"],
        "confidence": 0.84,
    },
    {
        "id": "systems-modeling",
        "hub": "Research",
        "article_map": "Systems Modeling",
        "discipline": "Systems Thinking",
        "content_type": "article_map",
        "patterns": ["systems modeling", "system dynamics", "modeling archives"],
        "confidence": 0.85,
    },
    {
        "id": "algorithms",
        "hub": "Research",
        "article_map": "Algorithms and Computational Reasoning",
        "discipline": "Computer Science",
        "content_type": "article",
        "patterns": ["/algorithms", "algorithms", "computational reasoning", "machine learning", "data structures"],
        "confidence": 0.88,
    },
    {
        "id": "international-law",
        "hub": "Research",
        "article_map": "International Law",
        "discipline": "Law",
        "content_type": "article",
        "patterns": ["/international-law", "international law", "war crimes", "genocide", "crimes against humanity", "human rights"],
        "confidence": 0.88,
    },
    {
        "id": "sustainability",
        "hub": "Research",
        "article_map": "Sustainability",
        "discipline": "Sustainable Development",
        "content_type": "article",
        "patterns": ["sustainable development", "sustainability", "climate", "energy systems", "environmental"],
        "confidence": 0.82,
    },
    {
        "id": "meaning",
        "hub": "Research",
        "article_map": "Meaning",
        "discipline": "Humanities",
        "content_type": "article",
        "patterns": ["/meaning/", "story myth", "myth", "meaning", "symbol", "ritual", "aesthetics"],
        "confidence": 0.86,
    },
    {
        "id": "channel",
        "hub": "Publications",
        "article_map": "Channel",
        "discipline": "Media",
        "content_type": "publication",
        "patterns": ["/channel/", "youtube", "spoken essays", "channel"],
        "confidence": 0.84,
    },
    {
        "id": "not-found",
        "hub": "System",
        "article_map": "Site Diagnostics",
        "discipline": "Operations",
        "content_type": "system",
        "patterns": ["page not found", "404", "/404"],
        "confidence": 0.96,
    },
]


class ContentRegistry:
    """Loads and maps Sustainable Catalyst content metadata.

    v0.1.2 adds inference-based classification so live GA4 pages can be
    interpreted even before every page is explicitly listed in the registry.
    """

    def __init__(self, registry_path: str):
        self.registry_path = Path(registry_path)
        if not self.registry_path.is_absolute():
            cwd_candidate = Path.cwd() / self.registry_path
            backend_candidate = Path.cwd() / "backend" / self.registry_path.name
            data_candidate = Path.cwd() / "data" / self.registry_path.name
            if cwd_candidate.exists():
                self.registry_path = cwd_candidate
            elif backend_candidate.exists():
                self.registry_path = backend_candidate
            elif data_candidate.exists():
                self.registry_path = data_candidate
        self.registry = self._load()
        self.by_path: Dict[str, ContentItem] = {self._norm(item.url_path): item for item in self.registry.items}

    @staticmethod
    def _norm(path: str) -> str:
        if not path:
            return "/"
        if path.startswith("http"):
            path = path.split("sustainablecatalyst.com", 1)[-1]
        path = path.split("?", 1)[0].split("#", 1)[0]
        if not path.startswith("/"):
            path = "/" + path
        if path != "/" and not path.endswith("/"):
            path += "/"
        return path

    @staticmethod
    def _slugify(value: str) -> str:
        value = value.lower().strip()
        value = re.sub(r"[^a-z0-9]+", "-", value)
        value = re.sub(r"-+", "-", value).strip("-")
        return value or "unmapped-page"

    def _load(self) -> Registry:
        if not self.registry_path.exists():
            return Registry(generated_at=datetime.now(timezone.utc).isoformat(), items=[])
        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        return Registry(**data)

    def find(self, path: str) -> Optional[ContentItem]:
        return self.resolve(path).item

    def explicit_find(self, path: str) -> Optional[ContentItem]:
        normalized = self._norm(path)
        exact = self.by_path.get(normalized)
        if exact:
            return exact
        candidates = [
            item for item in self.registry.items
            if self._norm(item.url_path) != "/" and normalized.startswith(self._norm(item.url_path))
        ]
        if not candidates:
            return None
        return sorted(candidates, key=lambda item: len(self._norm(item.url_path)), reverse=True)[0]

    def resolve(self, path: str, title: str = "") -> RegistryMatch:
        normalized = self._norm(path)
        explicit = self.explicit_find(normalized)
        if explicit:
            return RegistryMatch(item=explicit, status="explicit", confidence=1.0, reason="Explicit registry match.")
        if any(pattern in normalized for pattern in SYSTEM_PATH_PATTERNS):
            return RegistryMatch(item=None, status="excluded", confidence=1.0, reason="System or WordPress operational path.")
        inferred = self.infer_item(normalized, title)
        if inferred:
            return RegistryMatch(item=inferred[0], status="inferred", confidence=inferred[1], reason=inferred[2])
        return RegistryMatch(item=None, status="unmapped", confidence=0.0, reason="No explicit registry or inference rule matched.")

    def infer_item(self, path: str, title: str = "") -> Optional[tuple[ContentItem, float, str]]:
        text = f"{path} {title}".lower()
        best_rule = None
        best_hits: List[str] = []
        best_score = 0.0
        for rule in INFERENCE_RULES:
            hits = [pat for pat in rule["patterns"] if pat.lower() in text]
            if not hits:
                continue
            score = min(0.98, float(rule["confidence"]) + min(0.06, 0.015 * (len(hits) - 1)))
            if score > best_score:
                best_rule = rule
                best_hits = hits
                best_score = score
        if not best_rule:
            return None
        slug_source = path.strip("/").split("/")[-1] or title or best_rule["id"]
        item = ContentItem(
            id=f"inferred-{self._slugify(slug_source)}",
            title=title or slug_source.replace("-", " ").title(),
            url_path=path,
            content_type=str(best_rule["content_type"]),
            hub=str(best_rule["hub"]),
            article_map=best_rule.get("article_map"),
            discipline=best_rule.get("discipline"),
            pathway_id=f"inferred-{best_rule['id']}",
            tags=[str(best_rule["id"]), "inferred-mapping"],
        )
        return item, round(best_score, 2), f"Inferred from {', '.join(best_hits[:3])}."

    def suggestion_for_metric(self, metric) -> RegistrySuggestion:
        match = self.resolve(metric.path, metric.title)
        item = match.item
        if item is None:
            slug = self._slugify(metric.path.strip("/").split("/")[-1] or metric.title)
            item = ContentItem(
                id=slug,
                title=metric.title or slug.replace("-", " ").title(),
                url_path=self._norm(metric.path),
                content_type="article",
                hub="Unmapped",
                article_map=None,
                discipline=None,
                tags=["needs-review"],
            )
        return RegistrySuggestion(
            path=self._norm(metric.path),
            title=metric.title,
            suggested_id=self._slugify(item.id),
            suggested_hub=item.hub,
            suggested_article_map=item.article_map,
            suggested_content_type=item.content_type,
            suggested_discipline=item.discipline,
            confidence=match.confidence,
            reason=match.reason,
            sample_registry_item=item.model_dump(),
            views=metric.screen_page_views,
            active_users=metric.active_users,
        )

    def all_items(self) -> Iterable[ContentItem]:
        return self.registry.items

    def count(self) -> int:
        return len(self.registry.items)
