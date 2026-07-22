from types import SimpleNamespace
from pathlib import Path

import pytest

from app import economics_markets_sustainability as module


def settings(**overrides):
    values = {
        "platform_core_enabled": True,
        "platform_core_url": "https://core.example.test",
        "platform_core_public_api_key": "test-public-key",
        "economics_sustainability_enabled": True,
        "economics_sustainability_timeout_seconds": 9,
        "economics_sustainability_cache_ttl_seconds": 120,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def core_payload(records, total=None):
    return {
        "data": records,
        "meta": {"pagination": {"total": len(records) if total is None else total, "limit": 100, "offset": 0}},
    }


def record(**overrides):
    value = {
        "id": "economic-1",
        "source_record_id": "series:USA:2025",
        "source_id": "world-bank",
        "connector_id": "world-bank.indicators",
        "record_type": "macroeconomic_indicator",
        "subject": "National accounts",
        "indicator_code": "NY.GDP.MKTP.CD",
        "indicator_name": "GDP (current US$)",
        "dataset_id": "WDI",
        "geography_code": "USA",
        "geography_name": "United States",
        "period": "2025",
        "period_start": "2025-01-01T00:00:00Z",
        "frequency": "annual",
        "value_number": 30000000000000,
        "unit": "current US$",
        "status": "official_release",
        "published_at": "2026-01-20T00:00:00Z",
        "dimensions": {"safe": "value", "api_key": "must-not-leak"},
        "metadata": {"token": "must-not-leak"},
        "source_url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.CD",
        "license_name": "CC BY 4.0",
        "attribution": "World Bank",
        "content_hash": "sha256-value",
        "public": True,
    }
    value.update(overrides)
    return value


def test_unconfigured_core_returns_explicit_empty_state(monkeypatch):
    result = module.build_economics_overview(settings(platform_core_enabled=False, platform_core_url=""))
    assert result["ok"] is True
    assert result["integration"]["state"] == "core-unconfigured"
    assert result["counts"]["records_available"] == 0
    assert result["market_data_policy"]["licensed_real_time_exchange_data"] is False
    assert result["integration"]["credential_exposed"] is False


def test_record_proxy_sanitizes_credentials_and_classifies(monkeypatch):
    monkeypatch.setattr(module, "_core_json", lambda *args, **kwargs: core_payload([record()]))
    result = module.build_economic_records(settings(), limit=25)
    assert result["integration"]["state"] == "connected"
    item = result["records"][0]
    assert item["family"] == "macroeconomics"
    assert item["data_status"] == "OFFICIAL RELEASE"
    assert "api_key" not in item["dimensions"]
    assert "metadata" not in item
    assert "test-public-key" not in str(result)


def test_energy_and_sustainability_family_classification():
    energy = module._public_record(record(record_type="energy_statistic", subject="Electricity generation"))
    sustainability = module._public_record(record(record_type="official_statistic", subject="SDG climate emissions"))
    assert energy["family"] == "energy"
    assert sustainability["family"] == "sustainability"


def test_timing_labels_do_not_invent_real_time():
    assert module._data_status(record(status="official_release")) == "OFFICIAL RELEASE"
    assert module._data_status(record(status="", frequency="monthly")) == "MONTHLY"
    assert module._data_status(record(status="", frequency="quarterly")) == "QUARTERLY"
    assert "REAL TIME" not in module._data_status(record(status="real_time", frequency=""))


def test_series_is_sorted_and_preserves_source(monkeypatch):
    rows = [
        record(id="r2", period="2025", period_start="2025-01-01T00:00:00Z", value_number=2),
        record(id="r1", period="2024", period_start="2024-01-01T00:00:00Z", value_number=1),
    ]
    monkeypatch.setattr(module, "_core_json", lambda *args, **kwargs: core_payload(rows))
    result = module.build_economic_series(settings(), indicator_code="NY.GDP.MKTP.CD", geography_code="USA")
    assert [point["period"] for point in result["points"]] == ["2024", "2025"]
    assert result["latest"]["id"] == "r2"
    assert result["points"][0]["source_id"] == "world-bank"


def test_comparison_rejects_same_geography():
    with pytest.raises(ValueError):
        module.build_economic_comparison(settings(), indicator_code="GDP", geography_a="USA", geography_b="USA")


def test_public_interface_and_wordpress_contract():
    root = Path(__file__).resolve().parents[2]
    html = (root / "backend/public_app/index.html").read_text()
    js = (root / "backend/public_app/assets/economics-v220.js").read_text()
    css = (root / "backend/public_app/assets/economics-v220.css").read_text()
    app_js = (root / "backend/public_app/assets/app.js").read_text()
    php = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert 'data-route="economics"' in html
    assert 'id="economicsStudio"' in html
    assert "SCEconomicsV220" in js
    assert "licensed real-time" not in js.lower()
    assert ".economics-studio" in css
    assert 'const APP_VERSION="3.21.0"' in app_js
    assert "Version: 3.21.0" in php
    assert "sc_economics_sustainability_observatory" in php
