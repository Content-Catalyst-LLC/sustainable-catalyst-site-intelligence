from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.knowledge_graph_v2190 import KnowledgeGraphExplorer, SCHEMA_VERSION
from app.main import app


def settings(tmp_path: Path) -> Settings:
    return Settings(
        api_token="dev-token-change-me",
        knowledge_graph_entities_path=str(tmp_path / "entities.jsonl"),
        knowledge_graph_relationships_path=str(tmp_path / "relationships.jsonl"),
        knowledge_graph_aliases_path=str(tmp_path / "aliases.jsonl"),
        knowledge_graph_policy_path="backend/data/knowledge_graph_policy_v2190.json",
        knowledge_graph_relationship_registry_path="backend/data/knowledge_graph_relationship_registry_v2190.json",
        knowledge_graph_max_results=100,
    )


def entity(entity_id: str, entity_type: str, label: str, **overrides):
    value = {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "label": label,
        "visibility": "public",
        "status": "approved",
        "human_review_confirmed": True,
    }
    value.update(overrides)
    return value


def relation(relationship_id: str, relationship_type: str, source: str, target: str, **overrides):
    value = {
        "relationship_id": relationship_id,
        "relationship_type": relationship_type,
        "source_entity_id": source,
        "target_entity_id": target,
        "visibility": "public",
        "status": "approved",
        "human_review_confirmed": True,
        "evidence_ids": [f"evidence-{relationship_id}"],
        "confidence": "high",
        "confidence_score": 0.9,
    }
    value.update(overrides)
    return value


def seeded(tmp_path: Path) -> KnowledgeGraphExplorer:
    center = KnowledgeGraphExplorer(settings(tmp_path))
    center.register_entity(entity("country:ken", "country", "Kenya", aliases=["Republic of Kenya"], identifiers={"iso3": "KEN"}))
    center.register_entity(entity("indicator:population", "indicator", "Population"))
    center.register_entity(entity("source:world-bank", "source", "World Bank"))
    center.register_entity(entity("dataset:wb-pop", "dataset", "World Bank Population Dataset"))
    center.register_relationship(relation("r1", "published_by", "dataset:wb-pop", "source:world-bank"))
    center.register_relationship(relation("r2", "measures", "dataset:wb-pop", "indicator:population"))
    center.register_relationship(relation("r3", "observed_in", "dataset:wb-pop", "country:ken", valid_from="2020-01-01T00:00:00Z"))
    return center


def test_entity_registration_aliases_and_resolution(tmp_path):
    center = seeded(tmp_path)
    resolved = center.resolve("KEN", public=True, namespace="iso3")
    assert resolved["count"] == 1
    assert resolved["matches"][0]["entity"]["entity_id"] == "country:ken"
    label = center.resolve("Republic of Kenya", public=True)
    assert label["count"] == 1
    assert label["automatic_merge"] is False


def test_public_entities_require_human_review(tmp_path):
    center = KnowledgeGraphExplorer(settings(tmp_path))
    try:
        center.register_entity(entity("country:gha", "country", "Ghana", human_review_confirmed=False))
        assert False
    except ValueError as exc:
        assert "human_review_confirmed" in str(exc)


def test_relationships_require_evidence_and_valid_temporal_bounds(tmp_path):
    center = KnowledgeGraphExplorer(settings(tmp_path))
    center.register_entity(entity("country:ken", "country", "Kenya"))
    center.register_entity(entity("region:eaf", "region", "East Africa"))
    try:
        center.register_relationship(relation("bad", "located_in", "country:ken", "region:eaf", evidence_ids=[]))
        assert False
    except ValueError as exc:
        assert "requires evidence" in str(exc)
    try:
        center.register_relationship(relation("bad-time", "located_in", "country:ken", "region:eaf", valid_from="2025-01-01", valid_to="2024-01-01"))
        assert False
    except ValueError as exc:
        assert "valid_to" in str(exc)


def test_traversal_and_shortest_path_preserve_noncausal_boundary(tmp_path):
    center = seeded(tmp_path)
    traversal = center.traverse("source:world-bank", public=True, depth=3, direction="both")
    assert traversal["node_count"] == 4
    assert traversal["edge_count"] == 3
    assert traversal["causation_not_inferred"] is True
    path = center.shortest_path("source:world-bank", "country:ken", public=True, max_depth=4)
    assert path["found"] is True
    assert path["hop_count"] == 2
    assert path["causation_not_inferred"] is True


def test_temporal_filter_and_export(tmp_path):
    center = seeded(tmp_path)
    before = center.traverse("country:ken", public=True, depth=2, as_of="2019-01-01T00:00:00Z")
    assert before["edge_count"] == 0
    after = center.traverse("country:ken", public=True, depth=2, as_of="2022-01-01T00:00:00Z")
    assert after["edge_count"] == 3
    export = center.export_subgraph("country:ken", public=True, depth=3)
    assert export["read_only"] is True
    assert export["packet"]["packet_sha256"]
    assert "relationship_id,relationship_type" in export["csv"]


def test_reconciliation_is_preview_only_and_detects_alias_collisions(tmp_path):
    center = seeded(tmp_path)
    center.register_entity(entity("organization:ken", "organization", "Kenya Office", aliases=["Kenya"]))
    preview = center.preview_reconciliation({"queries": ["Kenya", "KEN"]}, public=True)
    assert preview["candidate_count"] == 2
    assert preview["automatic_merge"] is False
    assert preview["human_review_required"] is True
    diagnostics = center.diagnostics(public=True)
    assert diagnostics["automatic_merge"] is False


def test_platform_core_handoff_is_read_only(tmp_path):
    center = seeded(tmp_path)
    handoff = center.platform_core_handoff("country:ken", depth=2, public=True)
    assert handoff["destination"] == "platform-core"
    assert handoff["read_only"] is True
    assert handoff["write_performed"] is False


def test_public_and_admin_routes(tmp_path):
    cfg = settings(tmp_path)
    app.dependency_overrides[get_settings] = lambda: cfg
    try:
        client = TestClient(app)
        for path in ["/public/knowledge-graph", "/public/knowledge-graph/methodology", "/public/knowledge-graph/diagnostics", "/public/knowledge-graph/entities", "/admin/knowledge-graph/control-center"]:
            response = client.get(path)
            assert response.status_code == 200, (path, response.text)
        for body in [entity("country:ken", "country", "Kenya", aliases=["Republic of Kenya"], identifiers={"iso3": "KEN"}), entity("region:eaf", "region", "East Africa")]:
            assert client.post("/admin/knowledge-graph/entities/register", json=body).status_code == 200
        rel = relation("r-located", "located_in", "country:ken", "region:eaf")
        assert client.post("/admin/knowledge-graph/relationships/register", json=rel).status_code == 200
        assert client.get("/public/knowledge-graph/entities/country:ken").status_code == 200
        assert client.get("/public/knowledge-graph/resolve", params={"q": "KEN", "namespace": "iso3"}).json()["count"] == 1
        assert client.get("/public/knowledge-graph/traverse", params={"entity_id": "country:ken", "depth": 2}).json()["edge_count"] == 1
        assert client.get("/public/knowledge-graph/path", params={"source_id": "country:ken", "target_id": "region:eaf"}).json()["found"] is True
    finally:
        app.dependency_overrides.clear()


def test_public_summary_exposes_policy_boundaries(tmp_path):
    summary = KnowledgeGraphExplorer(settings(tmp_path)).public_summary()
    assert summary["schema"] == SCHEMA_VERSION
    assert summary["automatic_causation"] is False
    assert summary["automatic_entity_merge"] is False
    assert any("causation" in item.lower() for item in summary["boundaries"])
