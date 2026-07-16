from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.model_forecast_early_warning_v2170 import ModelForecastEarlyWarningCenter, SCHEMA_VERSION


def settings(tmp_path: Path) -> Settings:
    return Settings(
        api_token="dev-token-change-me",
        model_governance_root_path=str(tmp_path / "model"),
        model_governance_models_path=str(tmp_path / "models.jsonl"),
        model_governance_forecasts_path=str(tmp_path / "forecasts.jsonl"),
        model_governance_evaluations_path=str(tmp_path / "evaluations.jsonl"),
        model_governance_warning_rules_path=str(tmp_path / "rules.jsonl"),
        model_governance_warning_events_path=str(tmp_path / "events.jsonl"),
        model_governance_policy_path="backend/data/model_governance_policy_v2170.json",
        model_governance_metric_registry_path="backend/data/model_metric_registry_v2170.json",
    )


def model(**overrides):
    value = {
        "model_id": "heat-demand",
        "model_version": "1.0.0",
        "title": "Heat Demand Forecast",
        "model_type": "statistical",
        "provider": "Fixture Institute",
        "target": "daily heat demand",
        "frequency": "daily",
        "forecast_horizon": "7 days",
        "intended_use": "Analyst review of short-term heat demand.",
        "limitations": "Not an emergency warning and not validated outside the documented period.",
        "prohibited_uses": ["Emergency dispatch", "Individual targeting"],
        "uncertainty_method": "90 percent prediction interval",
        "visibility": "public",
        "status": "active",
    }
    value.update(overrides)
    return value


def forecast(**overrides):
    value = {
        "forecast_id": "heat-demand-2026-07-16",
        "model_id": "heat-demand",
        "model_version": "1.0.0",
        "issued_at": "2026-07-16T12:00:00+00:00",
        "confidence_level": 0.9,
        "visibility": "public",
        "values": [
            {"period": "2026-07-17", "value": 10, "lower": 8, "upper": 12},
            {"period": "2026-07-18", "value": 15, "lower": 12, "upper": 18},
            {"period": "2026-07-19", "value": 20, "lower": 16, "upper": 24},
            {"period": "2026-07-20", "value": 25, "lower": 20, "upper": 30},
        ],
    }
    value.update(overrides)
    return value


def test_model_card_requires_governance_fields_and_preserves_boundaries(tmp_path):
    center = ModelForecastEarlyWarningCenter(settings(tmp_path))
    result = center.register_model(model())
    card = result["model"]
    assert card["schema"].endswith("/1.0")
    assert card["human_review_required"] is True
    assert card["individual_level_data_allowed"] is False
    assert card["automatic_decision_authority"] is False
    assert card["model_card_sha256"]


def test_forecast_ingestion_requires_active_registered_model_and_declared_intervals(tmp_path):
    center = ModelForecastEarlyWarningCenter(settings(tmp_path))
    center.register_model(model())
    result = center.ingest_forecast(forecast())
    assert result["forecast"]["forecast_not_scenario"] is True
    assert result["forecast"]["forecast_sha256"]


def test_evaluation_computes_accuracy_calibration_and_drift_review(tmp_path):
    center = ModelForecastEarlyWarningCenter(settings(tmp_path))
    center.register_model(model())
    center.ingest_forecast(forecast())
    result = center.evaluate_forecast({
        "forecast_id": "heat-demand-2026-07-16",
        "visibility": "public",
        "baseline_count": 2,
        "drift_threshold": 1.5,
        "actuals": [
            {"period": "2026-07-17", "value": 10},
            {"period": "2026-07-18", "value": 14},
            {"period": "2026-07-19", "value": 30},
            {"period": "2026-07-20", "value": 40},
        ],
    })
    evaluation = result["evaluation"]
    assert evaluation["metrics"]["count"] == 4
    assert evaluation["metrics"]["mae"] > 0
    assert evaluation["interval_diagnostics"]["empirical_coverage"] == 0.5
    assert evaluation["drift"]["status"] == "review"
    assert evaluation["accuracy_not_guaranteed"] is True


def test_early_warning_thresholds_are_review_signals_not_emergency_actions(tmp_path):
    center = ModelForecastEarlyWarningCenter(settings(tmp_path))
    center.register_warning_rule({
        "rule_id": "heat-watch",
        "title": "Heat watch",
        "indicator": "daily heat demand",
        "direction": "above",
        "threshold": 20,
        "severity": "advisory",
        "visibility": "public",
    })
    result = center.evaluate_warning({"rule_id": "heat-watch", "values": [{"period": "2026-07-17", "value": 18}, {"period": "2026-07-18", "value": 24}]})
    assert result["status"] == "matched"
    event = result["event"]
    assert event["not_an_emergency_service"] is True
    assert event["causation_not_established"] is True
    assert event["severity"] == "advisory"


def test_public_boundary_filters_private_and_inactive_models(tmp_path):
    center = ModelForecastEarlyWarningCenter(settings(tmp_path))
    center.register_model(model())
    center.register_model(model(model_id="private-model", title="Private", visibility="private"))
    center.register_model(model(model_id="paused-model", title="Paused", status="paused"))
    public = center.models(public=True)
    assert [item["model_id"] for item in public["models"]] == ["heat-demand"]


def test_governance_export_is_digest_verified_and_read_only(tmp_path):
    center = ModelForecastEarlyWarningCenter(settings(tmp_path))
    center.register_model(model())
    center.ingest_forecast(forecast())
    export = center.export_governance_packet("heat-demand", public=True)
    assert export["read_only"] is True
    assert export["packet"]["packet_sha256"]
    assert "forecast_id,period,forecast,lower,upper" in export["csv"]


def test_model_governance_public_and_admin_routes(tmp_path):
    cfg = settings(tmp_path)
    app.dependency_overrides[get_settings] = lambda: cfg
    try:
        client = TestClient(app)
        for path in [
            "/public/model-governance",
            "/public/model-governance/methodology",
            "/public/model-governance/diagnostics",
            "/public/models",
            "/public/forecasts",
            "/public/forecast-evaluations",
            "/public/early-warning",
            "/admin/model-governance/control-center",
        ]:
            response = client.get(path)
            assert response.status_code == 200, (path, response.text)
        registered = client.post("/admin/model-governance/models/register", json=model())
        assert registered.status_code == 200
        ingested = client.post("/admin/model-governance/forecasts/ingest", json=forecast())
        assert ingested.status_code == 200
        evaluation = client.post("/admin/model-governance/evaluations/run", json={"forecast_id": "heat-demand-2026-07-16", "visibility": "public", "actuals": [{"period": "2026-07-17", "value": 11}]})
        assert evaluation.status_code == 200
        public = client.get("/public/models")
        assert public.json()["count"] == 1
    finally:
        app.dependency_overrides.clear()


def test_public_summary_exposes_schema_and_safety_boundaries(tmp_path):
    summary = ModelForecastEarlyWarningCenter(settings(tmp_path)).public_summary()
    assert summary["schema"] == SCHEMA_VERSION
    assert "No emergency-service claims" in summary["boundaries"]
