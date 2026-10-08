from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.predictive_spatial_consumer_v4520 import (
    CALIBRATION_CONTEXT_SCHEMA,
    COMPARISON_SCHEMA,
    MODEL_BINDING_SCHEMA,
    PREDICTIVE_OBJECT_SCHEMA,
    RESEARCH_CONTEXT_SCHEMA,
    SCENARIO_SCHEMA,
    bind_prediction,
    calibration_context,
    compare_predictions,
    compatibility_manifest,
    normalize_prediction,
    provider_manifest,
    query_predictions,
    registry_manifest,
    research_context,
    scenario_context,
    validate_prediction,
)
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.spatial_research_handoffs_v4510 import compose_research_object
from app.version import APP_VERSION, RELEASE_NAME

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def _prediction(*, model_id: str = "flood-model", scenario_id: str = "baseline", value: float = 0.72, bbox=None) -> dict:
    return {
        "target_layer_id": "hydrology-rivers-flood-drought",
        "target_metric": "flood_probability",
        "bbox": bbox or [-90.5, 38.4, -89.8, 38.9],
        "issued_at": "2026-10-05T12:00:00Z",
        "valid_time": {"start": "2026-10-06T00:00:00Z", "end": "2026-10-07T00:00:00Z"},
        "horizon": "24h",
        "model": {
            "model_id": model_id,
            "model_version": "2.3.0",
            "provider": "workspace",
            "model_type": "probabilistic-forecast",
            "model_digest": "sha256:" + "a" * 64,
            "execution_receipt_digest": "sha256:" + "b" * 64,
            "intended_use": "Regional flood-risk scenario analysis.",
            "limitations": "Model-conditional output; not an observed flood extent.",
        },
        "values": [
            {"period": "2026-10-06", "probability": value, "lower": 0.55, "upper": 0.84, "unit": "1"},
            {"period": "2026-10-07", "probability": max(0.0, value - 0.1), "lower": 0.42, "upper": 0.78, "unit": "1"},
        ],
        "scenario": {"scenario_id": scenario_id, "label": scenario_id.title(), "assumptions": ["Current forcing trajectory"]},
        "uncertainty": {"method": "prediction-interval", "level": 0.9},
        "calibration": {
            "status": "evaluated",
            "method": "rolling-origin",
            "metrics": {"brier_score": 0.14, "coverage_90": 0.88},
            "artifact_digest": "sha256:" + "c" * 64,
        },
        "provenance": {"source_product": "workspace", "runtime": "forecast"},
        "source_evidence_digests": ["sha256:" + "d" * 64],
    }


def _research_object() -> dict:
    return compose_research_object({
        "title": "Flood exposure research",
        "research_question": "Which infrastructure is potentially exposed?",
        "scope": {"countries": ["USA"], "bbox": [-90.5, 38.4, -89.8, 38.9]},
        "evidence_objects": [{"object_id": "hydrology-a", "content_digest": "sha256:" + "e" * 64}],
        "uncertainties": ["Prediction does not confirm impact."],
    })["research_object"]


def test_release_identity() -> None:
    assert APP_VERSION == "4.55.3.2.2"
    assert RELEASE_NAME == "Browser API Transport & CORS Repair"


def test_registry_declares_four_provider_classes_and_boundaries() -> None:
    payload = registry_manifest()
    assert payload["provider_count"] == 4
    ids = {row["provider_id"] for row in payload["providers"]}
    assert ids == {"workspace", "platform-core", "site-intelligence-model-governance", "external-published"}
    assert "site-intelligence-is-a-consumer-not-model-training-authority" in payload["boundaries"]


def test_provider_manifest_is_machine_readable() -> None:
    payload = provider_manifest()
    assert payload["count"] == 4
    workspace = next(row for row in payload["providers"] if row["provider_id"] == "workspace")
    assert workspace["network_fetch_by_site_intelligence"] is False


def test_normalization_is_deterministic_and_model_conditional() -> None:
    a = normalize_prediction(_prediction())["prediction"]
    b = normalize_prediction(_prediction())["prediction"]
    assert a["schema"] == PREDICTIVE_OBJECT_SCHEMA
    assert a["prediction_digest"] == b["prediction_digest"]
    assert a["prediction_id"] == b["prediction_id"]
    assert a["object_type"] == "model-conditional-prediction"
    assert a["target_domain"] == "hydrology"
    assert "probability-is-not-truth" in a["boundaries"]


def test_validation_detects_tampering() -> None:
    obj = normalize_prediction(_prediction())["prediction"]
    assert validate_prediction(obj)["valid"] is True
    obj["values"][0]["probability"] = 0.01
    result = validate_prediction(obj)
    assert result["valid"] is False
    assert "prediction-digest-mismatch" in result["errors"]


def test_missing_uncertainty_and_calibration_are_warnings_not_fabricated() -> None:
    req = _prediction()
    req.pop("uncertainty")
    req.pop("calibration")
    obj = normalize_prediction(req)["prediction"]
    result = validate_prediction(obj)
    assert result["valid"] is True
    assert "uncertainty-context-missing" in result["warnings"]
    assert "calibration-context-missing" in result["warnings"]


def test_spatial_binding_preserves_prediction_and_does_not_claim_impact() -> None:
    prediction = normalize_prediction(_prediction())["prediction"]
    result = bind_prediction({
        "prediction": prediction,
        "evidence_objects": [
            {"object_id": "substation-a", "layer_id": "energy-power-systems", "bbox": [-90.2, 38.6, -90.1, 38.7], "content_digest": "sha256:" + "f" * 64},
            {"object_id": "far-away", "layer_id": "energy-power-systems", "bbox": [-100.2, 40.6, -100.1, 40.7], "content_digest": "sha256:" + "1" * 64},
        ],
    })["binding"]
    assert result["schema"] == MODEL_BINDING_SCHEMA
    assert result["binding_count"] == 1
    assert result["bindings"][0]["impact_confirmed"] is False
    assert result["prediction_digest"] == prediction["prediction_digest"]


def test_query_filters_space_time_provider_and_model() -> None:
    a = normalize_prediction(_prediction(model_id="m-a"))["prediction"]
    b = normalize_prediction(_prediction(model_id="m-b", bbox=[-120.0, 35.0, -119.0, 36.0]))["prediction"]
    result = query_predictions({
        "predictions": [a, b],
        "filters": {"model_ids": ["m-a"], "providers": ["workspace"], "bbox": [-91, 38, -89, 39], "start": "2026-10-06T00:00:00Z", "end": "2026-10-06T23:00:00Z"},
    })["result"]
    assert result["count"] == 1
    assert result["predictions"][0]["model"]["model_id"] == "m-a"
    assert result["result_digest"].startswith("sha256:")


def test_comparison_does_not_rank_or_select_model() -> None:
    a = normalize_prediction(_prediction(model_id="m-a", value=0.72))["prediction"]
    b = normalize_prediction(_prediction(model_id="m-b", value=0.64))["prediction"]
    result = compare_predictions({"predictions": [a, b]})["comparison"]
    assert result["schema"] == COMPARISON_SCHEMA
    assert result["automatic_model_ranking"] is False
    assert result["preferred_prediction"] is None
    assert result["human_review_required"] is True


def test_comparison_requires_common_target_layer() -> None:
    a = normalize_prediction(_prediction(model_id="m-a"))["prediction"]
    req = _prediction(model_id="m-b")
    req["target_layer_id"] = "energy-power-systems"
    b = normalize_prediction(req)["prediction"]
    with pytest.raises(ValueError):
        compare_predictions({"predictions": [a, b]})


def test_scenario_context_preserves_alternatives_without_selecting() -> None:
    baseline = normalize_prediction(_prediction(model_id="m-a", scenario_id="baseline"))["prediction"]
    high = normalize_prediction(_prediction(model_id="m-a", scenario_id="high-forcing", value=0.86))["prediction"]
    result = scenario_context({"predictions": [baseline, high]})["scenario_context"]
    assert result["schema"] == SCENARIO_SCHEMA
    assert result["scenario_count"] == 2
    assert result["automatic_scenario_selection"] is False
    assert result["preferred_scenario"] is None


def test_calibration_context_is_consumed_not_recomputed() -> None:
    prediction = normalize_prediction(_prediction())["prediction"]
    result = calibration_context({"prediction": prediction})["calibration_context"]
    assert result["schema"] == CALIBRATION_CONTEXT_SCHEMA
    assert result["status"] == "evaluated"
    assert result["metrics"]["brier_score"] == 0.14
    assert result["consumer_recomputed_metrics"] is False
    assert result["calibration_is_evidence_not_guarantee"] is True


def test_research_context_links_without_mutating_research_object() -> None:
    research = _research_object()
    prediction = normalize_prediction(_prediction())["prediction"]
    before = json.dumps(research, sort_keys=True)
    context = research_context({"research_object": research, "predictions": [prediction]})["research_context"]
    assert context["schema"] == RESEARCH_CONTEXT_SCHEMA
    assert context["research_digest"] == research["research_digest"]
    assert context["research_object_mutated"] is False
    assert json.dumps(research, sort_keys=True) == before


def test_sensitive_fields_are_rejected() -> None:
    req = _prediction()
    req["provenance"] = {"api_key": "not-allowed"}
    with pytest.raises(ValueError):
        normalize_prediction(req)


def test_probability_bounds_are_enforced() -> None:
    req = _prediction()
    req["values"][0]["probability"] = 1.5
    with pytest.raises(ValueError):
        normalize_prediction(req)


def test_http_routes_and_error_boundary() -> None:
    assert client.get("/public/predictive-spatial/registry").status_code == 200
    assert client.get("/public/predictive-spatial/schema").json()["schema"] == PREDICTIVE_OBJECT_SCHEMA
    assert client.get("/public/predictive-spatial/providers").json()["count"] == 4
    normalized = client.post("/public/predictive-spatial/normalize", json=_prediction())
    assert normalized.status_code == 200
    prediction = normalized.json()["prediction"]
    assert client.post("/public/predictive-spatial/validate", json=prediction).json()["valid"] is True
    assert client.post("/public/predictive-spatial/bind", json={"prediction": prediction, "evidence_objects": []}).status_code == 200
    assert client.post("/public/predictive-spatial/query", json={"predictions": [prediction]}).status_code == 200
    assert client.post("/public/predictive-spatial/compare", json={"predictions": [prediction]}).status_code == 400
    assert client.post("/public/predictive-spatial/scenario", json={"predictions": [prediction]}).status_code == 200
    assert client.post("/public/predictive-spatial/calibration", json={"prediction": prediction}).status_code == 200
    assert client.post("/public/predictive-spatial/research-context", json={"research_object": _research_object(), "predictions": [prediction]}).status_code == 200
    assert client.get("/public/predictive-spatial/compatibility").status_code == 200


def test_compatibility_preserves_prior_stack_and_legacy_model_governance() -> None:
    compat = compatibility_manifest()
    assert compat["v4_46_spatial_evidence"]["prediction_is_observation"] is False
    assert compat["v4_48_spatial_graph"]["automatic_causal_edges_from_prediction"] is False
    assert compat["v4_51_spatial_research"]["research_object_mutation"] is False
    assert "/public/forecasts" in compat["legacy_model_governance"]["routes"]
    assert compat["model_training_authority"] is False
    assert compat["automatic_model_selection"] is False


def test_capability_registry_owns_predictive_routes() -> None:
    manifest = capability_manifest(app.routes)
    family = next(row for row in manifest["capabilities"] if row["capability_id"] == "predictive-spatial-intelligence")
    assert manifest["registry_version"] == "2.6.2"
    assert manifest["route_count"] == 1518
    assert manifest["modularized_route_count"] == 209
    assert manifest["capability_count"] == 31
    assert manifest["unclassified_route_count"] == 0
    assert family["route_count"] == 12
    assert family["modularized_route_count"] == 12
    inventory = route_inventory(app.routes)
    rows = [row for row in inventory if row["capability_id"] == "predictive-spatial-intelligence"]
    assert len(rows) == 12
    assert all(row["modularized"] for row in rows)
    keys = [(method, row["path"]) for row in inventory for method in row["methods"]]
    assert len(keys) == len(set(keys))


def test_release_bound_predictive_registry_and_prior_registries_are_current() -> None:
    names = [
        "predictive_spatial_consumer_registry_v4520.json",
        "spatial_research_handoff_registry_v4510.json",
        "global_source_federation_registry_v4500.json",
        "live_geospatial_event_fusion_registry_v4490.json",
        "spatial_relationship_registry_v4480.json",
        "spatiotemporal_operator_registry_v4470.json",
        "spatial_layer_registry_v4460.json",
    ]
    for name in names:
        payload = json.loads((ROOT / "backend/data" / name).read_text())
        assert payload["version"] == APP_VERSION, name
    registry = json.loads((ROOT / "backend/data/predictive_spatial_consumer_registry_v4520.json").read_text())
    assert registry["schema"] == "sc-site-intelligence-predictive-spatial-consumer-registry/1.0"
    assert len(registry["providers"]) == 4


def test_wordpress_remains_thin_shell_without_predictive_shortcode() -> None:
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert "Version: 4.55.3.2.2" in php
    assert "const VERSION = '4.55.3.2.2';" in php
    assert "const WORDPRESS_ROLE = 'public-site-launch-bridge';" in php
    assert "predictive_spatial_shortcode" not in php
