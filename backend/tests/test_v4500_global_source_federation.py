from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.global_source_federation_v4500 import (
    FEDERATION_PLAN_SCHEMA,
    REGISTRY_SCHEMA,
    SELECTION_SCHEMA,
    SOURCE_SCHEMA,
    TRUST_EVALUATION_SCHEMA,
    evaluate_trust_profile,
    federation_plan,
    jurisdiction_manifest,
    select_source,
    source_detail,
    source_manifest,
)
from app.main import app
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.version import APP_VERSION, RELEASE_NAME

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_release_identity() -> None:
    assert APP_VERSION == "4.55.3"
    assert RELEASE_NAME == "Standalone Web Application Foundation & WordPress Decoupling"


def test_registry_and_authority_contracts_are_machine_readable() -> None:
    registry = client.get("/public/source-federation/registry")
    assert registry.status_code == 200
    payload = registry.json()
    assert payload["schema"] == REGISTRY_SCHEMA
    assert payload["version"] == APP_VERSION
    assert payload["source_count"] == 24
    assert payload["authority_class_count"] == 10
    assert payload["regional_group_count"] == 7
    assert payload["selection_policy"]["semantic_compatibility_required"] is True
    assert payload["trust_policy"]["separate_from_authority"] is True
    assert payload["trust_policy"]["separate_from_quality"] is True

    authority_types = client.get("/public/source-federation/authority-types").json()
    assert authority_types["count"] == 10
    ids = {row["id"] for row in authority_types["authority_classes"]}
    assert {"national-statistical-authority", "intergovernmental-custodian", "open-community-supplemental"} <= ids


def test_authority_catalog_filters_by_domain_jurisdiction_language_and_mode() -> None:
    usa_weather = source_manifest(jurisdiction="USA", domain="weather")
    ids = {row["source_id"] for row in usa_weather["sources"]}
    assert "noaa_nws" in ids
    assert "copernicus-era5" in ids
    assert "pcbs-pxweb" not in ids

    arabic_pse = source_manifest(jurisdiction="PSE", language="ar")
    ids = {row["source_id"] for row in arabic_pse["sources"]}
    assert {"pcbs-pxweb", "pcbs-pxweb-sdgs"} <= ids

    discovery = source_manifest(federation_mode="discovery")
    assert {row["source_id"] for row in discovery["sources"]} == {"nasa-cmr"}


def test_source_detail_preserves_authority_quality_and_discovery_boundary() -> None:
    nasa = source_detail("nasa-cmr")
    assert nasa["schema"] == SOURCE_SCHEMA
    assert nasa["source"]["authority_class"] == "scientific-observatory"
    assert nasa["boundaries"]["discovery_mode_is_not_observation"] is True
    assert nasa["boundaries"]["authority_is_not_user_trust"] is True
    with pytest.raises(ValueError):
        source_detail("not-a-source")


def test_regions_and_jurisdictions_expose_eligible_authorities() -> None:
    regions = client.get("/public/source-federation/regions").json()
    europe = next(row for row in regions["regions"] if row["region_id"] == "europe")
    assert europe["country_count"] > 0
    assert europe["regional_authority_count"] >= 1

    pse = jurisdiction_manifest("PSE")
    ids = {row["source_id"] for row in pse["eligible_sources"]}
    assert {"pcbs-pxweb", "pcbs-pxweb-sdgs", "world_bank"} <= ids
    assert any(row["concept_id"] == "electricity_structural_access" for row in pse["precedence_rules"])
    assert "exact semantic" in pse["precedence_boundary"]

    with pytest.raises(ValueError):
        jurisdiction_manifest("ZZZ")


def test_semantic_incompatibility_is_excluded_before_authority_or_freshness() -> None:
    result = select_source({
        "jurisdiction": "CAN",
        "concept_id": "population_total",
        "candidates": [
            {"source_id": "statistics-canada-wds", "semantic_compatible": True, "freshness_state": "aging", "record_status": "final"},
            {"source_id": "world_bank", "semantic_compatible": False, "freshness_state": "fresh", "record_status": "final"},
        ],
    })
    assert result["schema"] == SELECTION_SCHEMA
    assert result["selected_source_id"] == "statistics-canada-wds"
    assert any(row["source_id"] == "world_bank" and row["reason"] == "semantic-incompatibility" for row in result["excluded"])


def test_declared_pse_precedence_selects_national_exact_concept_source() -> None:
    result = select_source({
        "jurisdiction": "PSE",
        "concept_id": "electricity_structural_access",
        "candidates": [
            {"source_id": "world_bank", "semantic_compatible": True, "freshness_state": "fresh", "record_status": "final"},
            {"source_id": "pcbs-pxweb-sdgs", "semantic_compatible": True, "freshness_state": "aging", "record_status": "final"},
        ],
    })
    assert result["selected_source_id"] == "pcbs-pxweb-sdgs"
    assert result["selection_components"]["declared_precedence_rule"]["preferred_sources"][0] == "pcbs-pxweb-sdgs"
    assert result["authority_mutated_by_trust"] is False


def test_user_trust_can_filter_but_never_rewrites_source_authority_or_quality() -> None:
    trust = evaluate_trust_profile({
        "source_ids": ["pcbs-pxweb-sdgs", "world_bank"],
        "trust_profile": {"blocked_source_ids": ["pcbs-pxweb-sdgs"]},
    })
    assert trust["schema"] == TRUST_EVALUATION_SCHEMA
    assert trust["authority_mutated"] is False
    assert trust["quality_mutated"] is False
    pcbs = next(row for row in trust["evaluations"] if row["source_id"] == "pcbs-pxweb-sdgs")
    assert pcbs["accepted"] is False
    assert pcbs["authority_class_unchanged"] == "national-statistical-authority"

    result = select_source({
        "jurisdiction": "PSE",
        "concept_id": "electricity_structural_access",
        "trust_profile": {"blocked_source_ids": ["pcbs-pxweb-sdgs"]},
        "candidates": [
            {"source_id": "pcbs-pxweb-sdgs", "semantic_compatible": True, "freshness_state": "fresh", "record_status": "final"},
            {"source_id": "world_bank", "semantic_compatible": True, "freshness_state": "fresh", "record_status": "final"},
        ],
    })
    assert result["selected_source_id"] == "world_bank"
    assert any(row["source_id"] == "pcbs-pxweb-sdgs" and row["reason"] == "user-trust-profile-filter" for row in result["excluded"])


def test_federation_plan_is_preview_only_and_does_not_fetch_or_import() -> None:
    plan = federation_plan({
        "jurisdiction": "USA",
        "domains": ["weather", "hydrology"],
        "federation_modes": ["live", "auth-required"],
    })
    assert plan["schema"] == FEDERATION_PLAN_SCHEMA
    ids = {row["source_id"] for row in plan["sources"]}
    assert {"noaa_nws", "usgs-water-ogc"} <= ids
    assert plan["execution"] == {
        "network_calls_performed": False,
        "automatic_import_performed": False,
        "automatic_remote_write_performed": False,
        "plan_only": True,
    }
    assert plan["plan_digest"].startswith("sha256:")


def test_federation_plan_is_deterministic() -> None:
    request = {"jurisdiction": "GBR", "domains": ["population", "economics"]}
    assert federation_plan(request)["plan_digest"] == federation_plan(request)["plan_digest"]


def test_http_routes_enforce_errors_and_expose_compatibility() -> None:
    unknown = client.get("/public/source-federation/authorities/not-a-source")
    assert unknown.status_code == 400
    bad_select = client.post("/public/source-federation/select", json={"candidates": []})
    assert bad_select.status_code == 400
    bad_jurisdiction = client.post("/public/source-federation/federate", json={"jurisdiction": "ZZZ"})
    assert bad_jurisdiction.status_code == 400

    compat = client.get("/public/source-federation/compatibility").json()
    assert compat["v4_35_source_precedence"]["status"] == "preserved-and-consumed"
    assert compat["v4_49_live_geospatial"]["status"] == "preserved"
    assert compat["institutional_federation_v2240"]["automatic_remote_fetch"] is False
    assert compat["wordpress_role"] == "public-site-launch-bridge"


def test_capability_registry_owns_all_source_federation_routes() -> None:
    manifest = capability_manifest(app.routes)
    family = next(row for row in manifest["capabilities"] if row["capability_id"] == "global-source-federation")
    assert manifest["registry_version"] == "2.4.0"
    assert manifest["route_count"] == 1506
    assert manifest["modularized_route_count"] == 197
    assert manifest["capability_count"] == 29
    assert manifest["unclassified_route_count"] == 0
    assert family["route_count"] == 10
    assert family["modularized_route_count"] == 10
    inventory = route_inventory(app.routes)
    rows = [row for row in inventory if row["capability_id"] == "global-source-federation"]
    assert len(rows) == 10
    assert all(row["modularized"] for row in rows)
    keys = [(method, row["path"]) for row in inventory for method in row["methods"]]
    assert len(keys) == len(set(keys))


def test_release_bound_source_registry_and_carried_forward_registries_are_current() -> None:
    names = [
        "global_source_federation_registry_v4500.json",
        "live_geospatial_event_fusion_registry_v4490.json",
        "spatial_relationship_registry_v4480.json",
        "spatiotemporal_operator_registry_v4470.json",
        "spatial_layer_registry_v4460.json",
        "live_intelligence_source_registry_v320.json",
        "federation_policy_v2240.json",
        "country_identity_registry_v43523.json",
    ]
    for name in names:
        payload = json.loads((ROOT / "backend/data" / name).read_text())
        assert payload["version"] == APP_VERSION, name
    federation = json.loads((ROOT / "backend/data/global_source_federation_registry_v4500.json").read_text())
    assert federation["schema"] == REGISTRY_SCHEMA
    assert len(federation["sources"]) == 24
    assert federation["trust_policy"]["separate_from_authority"] is True


def test_wordpress_remains_thin_shell_and_no_new_feature_shortcode_is_added() -> None:
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert "Version: 4.55.3" in php
    assert "const VERSION = '4.55.3';" in php
    assert "const WORDPRESS_ROLE = 'public-site-launch-bridge';" in php
    assert "source_federation_shortcode" not in php
