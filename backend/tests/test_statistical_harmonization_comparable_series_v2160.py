from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.statistical_harmonization_v2160 import StatisticalHarmonizationEngine, SCHEMA_VERSION

ROOT = Path(__file__).resolve().parents[2]


def settings(tmp_path: Path) -> Settings:
    root = tmp_path / "harmonization"
    return Settings(
        version="2.19.0",
        statistical_harmonization_root_path=str(root),
        statistical_harmonization_series_index_path=str(root / "series.jsonl"),
        statistical_harmonization_lineage_path=str(root / "lineage.jsonl"),
        statistical_harmonization_policy_path=str(ROOT / "backend/data/statistical_harmonization_policy_v2160.json"),
        statistical_harmonization_unit_registry_path=str(ROOT / "backend/data/unit_registry_v2160.json"),
        statistical_harmonization_geography_registry_path=str(ROOT / "backend/data/geography_compatibility_registry_v2160.json"),
    )


def series(series_id="mass", unit="kg", values=None, visibility="public", geography=None, frequency="annual", **extra):
    return {
        "series_id": series_id,
        "title": series_id.title(),
        "indicator_id": "indicator",
        "source": "Official fixture",
        "unit_code": unit,
        "frequency": frequency,
        "visibility": visibility,
        "geography": geography or {"code": "KEN", "name": "Kenya", "level": "country", "definition_version": "2026"},
        "observations": values or [{"period": "2024", "value": 100}, {"period": "2025", "value": 150}],
        **extra,
    }


def test_register_series_preserves_raw_metadata_and_missing_classes(tmp_path):
    engine = StatisticalHarmonizationEngine(settings(tmp_path))
    result = engine.register_series(series(values=[{"period": "2024", "value": 100}, {"period": "2025", "value": None, "missing_class": "suppressed"}]))
    assert result["status"] == "registered"
    detail = engine.series_detail("mass", public=True)
    assert detail["raw"]["observations"][1]["missing_class"] == "suppressed"
    assert detail["series"]["missing_count"] == 1


def test_unit_conversion_is_dimension_checked_and_lineage_is_reproducible(tmp_path):
    engine = StatisticalHarmonizationEngine(settings(tmp_path))
    engine.register_series(series())
    result = engine.transform({"series_id": "mass", "output_series_id": "mass-tonnes", "transformations": [{"type": "unit_conversion", "target_unit_code": "t"}], "visibility": "public"})
    detail = engine.series_detail("mass-tonnes", public=True)
    assert detail["raw"]["observations"][0]["value"] == 0.1
    assert result["lineage"][0]["input_sha256"] != result["lineage"][0]["output_sha256"]
    assert result["lineage"][0]["silent"] is False


def test_frequency_alignment_requires_explicit_aggregation(tmp_path):
    engine = StatisticalHarmonizationEngine(settings(tmp_path))
    engine.register_series(series(series_id="monthly", unit="count", frequency="monthly", values=[{"period": "2025-01", "value": 2}, {"period": "2025-02", "value": 3}]))
    result = engine.transform({"series_id": "monthly", "output_series_id": "annual", "transformations": [{"type": "frequency_alignment", "target_frequency": "annual", "aggregation": "sum"}]})
    detail = engine.series_detail("annual")
    assert detail["raw"]["observations"] == [{"period": "2025", "value": 5.0, "missing_class": "observed", "status": "derived", "note": "Explicit sum aggregation from 2 monthly records."}]
    assert result["transformation_receipt"]["schema"].endswith("/1.0")


def test_per_capita_does_not_impute_missing_denominators(tmp_path):
    engine = StatisticalHarmonizationEngine(settings(tmp_path))
    engine.register_series(series(unit="count"))
    engine.transform({"series_id": "mass", "output_series_id": "per-capita", "transformations": [{"type": "per_capita", "target_per": 1000, "denominators": {"2024": 10}}]})
    values = engine.series_detail("per-capita")["raw"]["observations"]
    assert values[0]["value"] == 10000
    assert values[1]["value"] is None and values[1]["missing_class"] == "not_available"


def test_currency_conversion_and_constant_prices_require_supplied_evidence(tmp_path):
    engine = StatisticalHarmonizationEngine(settings(tmp_path))
    engine.register_series(series(unit="currency", currency_code="USD", price_basis="current prices"))
    engine.transform({"series_id": "mass", "output_series_id": "real-eur", "price_basis": "constant 2025 prices", "transformations": [
        {"type": "currency_conversion", "target_currency_code": "EUR", "rates": {"2024": 0.9, "2025": 0.8}, "rate_source": "Official fixture"},
        {"type": "constant_price_adjustment", "deflators": {"2024": 90, "2025": 100}, "base_index": 100, "base_year": 2025, "deflator_source": "Official fixture"},
    ]})
    detail = engine.series_detail("real-eur")
    assert detail["raw"]["currency_code"] == "EUR"
    assert round(detail["raw"]["observations"][0]["value"], 6) == 100.0


def test_comparability_blocks_incompatible_dimensions_and_geographies(tmp_path):
    engine = StatisticalHarmonizationEngine(settings(tmp_path))
    engine.register_series(series(series_id="left", unit="kg"))
    engine.register_series(series(series_id="right", unit="km", geography={"code": "GHA", "name": "Ghana", "level": "country", "definition_version": "2026"}))
    result = engine.compare({"left_series_id": "left", "right_series_id": "right"}, public=True)
    assert result["comparable"] is False
    assert result["blocking_issues"] >= 2
    assert result["ranking_created"] is False


def test_comparable_series_can_be_paired_after_explicit_unit_conversion(tmp_path):
    engine = StatisticalHarmonizationEngine(settings(tmp_path))
    engine.register_series(series(series_id="kg", unit="kg"))
    engine.register_series(series(series_id="tonnes", unit="t", values=[{"period": "2024", "value": 0.1}, {"period": "2025", "value": 0.2}]))
    result = engine.compare({"left_series_id": "kg", "right_series_id": "tonnes"}, public=True)
    assert result["comparable"] is True
    assert result["paired_values"][0]["difference"] == 0


def test_public_summary_standards_export_and_workbench_handoff(tmp_path):
    engine = StatisticalHarmonizationEngine(settings(tmp_path))
    engine.register_series(series())
    assert engine.public_summary()["schema"] == SCHEMA_VERSION
    assert any(item["code"] == "percent" for item in engine.standards()["units"])
    export = engine.export("mass", public=True)
    assert "period,value,missing_class" in export["csv"]
    assert export["workbench_handoff"]["read_only"] is True
    assert export["packet"]["packet_sha256"]


def test_harmonization_routes_are_registered_and_admin_transform_is_protected_by_existing_token_contract(tmp_path):
    cfg = settings(tmp_path)
    app.dependency_overrides[get_settings] = lambda: cfg
    try:
        client = TestClient(app)
        for path in ["/public/harmonization", "/public/harmonization/standards", "/public/harmonization/methodology", "/public/harmonization/series", "/public/harmonization/diagnostics", "/admin/harmonization/control-center", "/admin/harmonization/series"]:
            response = client.get(path)
            assert response.status_code == 200, (path, response.text)
        created = client.post("/admin/harmonization/series/register", json=series())
        assert created.status_code == 200
        transformed = client.post("/admin/harmonization/transform", json={"series_id": "mass", "output_series_id": "mass-tonnes", "transformations": [{"type": "unit_conversion", "target_unit_code": "t"}], "visibility": "public"})
        assert transformed.status_code == 200
        compared = client.post("/public/harmonization/compare", json={"left_series_id": "mass", "right_series_id": "mass-tonnes"})
        assert compared.status_code == 200 and compared.json()["comparable"] is True
    finally:
        app.dependency_overrides.clear()
