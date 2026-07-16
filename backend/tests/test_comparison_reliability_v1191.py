from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app import comparative_intelligence as comparison


COUNTRIES = {
    "KEN": {
        "code": "KEN",
        "iso2": "KE",
        "name": "Kenya",
        "region": "Sub-Saharan Africa",
        "capital": "Nairobi",
        "latitude": 0.0236,
        "longitude": 37.9062,
    },
    "GHA": {
        "code": "GHA",
        "iso2": "GH",
        "name": "Ghana",
        "region": "Sub-Saharan Africa",
        "capital": "Accra",
        "latitude": 7.9465,
        "longitude": -1.0232,
    },
    "USA": {
        "code": "USA",
        "iso2": "US",
        "name": "United States",
        "region": "North America",
        "capital": "Washington, D.C.",
        "latitude": 38.0,
        "longitude": -97.0,
    },
}


def indicator(
    indicator_id: str,
    key: str,
    label: str,
    value: float | None,
    year: int | None,
    unit: str,
    *,
    source: str = "World Bank Open Data",
    source_id: str | None = None,
    source_url: str | None = None,
    state: str = "live",
    series: list[dict] | None = None,
):
    latest = None if value is None else {"value": value, "year": year}
    return {
        "id": indicator_id,
        "key": key,
        "label": label,
        "domain": "Test domain",
        "unit": unit,
        "format": "decimal",
        "source": source,
        "source_id": source_id or indicator_id,
        "source_url": source_url or f"https://data.worldbank.org/indicator/{indicator_id}",
        "data_state": state if latest else "unavailable",
        "cache_state": state,
        "retrieved_at": "2026-07-11T00:00:00+00:00",
        "stale": state == "stale",
        "latest": latest,
        "series": series if series is not None else ([] if latest is None else [
            {"year": year - 1, "value": value - 1},
            {"year": year, "value": value},
        ]),
    }


def country_payload(code: str):
    if code == "KEN":
        rows = [
            indicator("SP.POP.TOTL", "population", "Population", 55.0, 2023, "people"),
            indicator("SP.DYN.LE00.IN", "life_expectancy", "Life expectancy", 66.7, 2022, "years"),
            indicator("EG.ELC.ACCS.ZS", "electricity_access", "Electricity access", None, None, "% of population"),
            indicator("UNIT.TEST", "unit_test", "Unit test", 10, 2023, "people"),
            indicator("SOURCE.TEST", "source_test", "Source test", 5, 2023, "index"),
            indicator(
                "GAP.TEST",
                "gap_test",
                "Gap test",
                3,
                2023,
                "index",
                series=[{"year": 2020, "value": 1}, {"year": 2022, "value": 2}, {"year": 2023, "value": 3}],
            ),
        ]
    else:
        rows = [
            indicator("SP.POP.TOTL", "population", "Population", 34.0, 2023, "persons"),
            indicator("SP.DYN.LE00.IN", "life_expectancy", "Life expectancy", 64.5, 2021, "years"),
            indicator("EG.ELC.ACCS.ZS", "electricity_access", "Electricity access", 89.5, 2022, "% of population", source="World Bank reference snapshot", state="reference-snapshot"),
            indicator("UNIT.TEST", "unit_test", "Unit test", 12, 2023, "years"),
            indicator(
                "SOURCE.TEST",
                "source_test",
                "Source test",
                6,
                2023,
                "index",
                source="Other Publisher",
                source_id="OTHER.SOURCE.TEST",
                source_url="https://example.org/source-test",
            ),
            indicator(
                "GAP.TEST",
                "gap_test",
                "Gap test",
                4,
                2023,
                "index",
                series=[{"year": 2021, "value": 2}, {"year": 2022, "value": 3}, {"year": 2023, "value": 4}],
            ),
        ]
    return {
        "ok": True,
        "version": "2.21.0",
        "country": COUNTRIES[code],
        "data_state": "live",
        "indicators": rows,
    }


def events(*, country_code: str, **_kwargs):
    return {
        "ok": True,
        "version": "2.21.0",
        "data_state": "live",
        "country_code": country_code,
        "count": 1,
        "events": [{"id": f"{country_code}-1", "title": "Event", "country_code": country_code}],
    }


def install(monkeypatch):
    monkeypatch.setattr(comparison, "country_catalog", lambda: {"countries": list(COUNTRIES.values())})
    monkeypatch.setattr(comparison, "country_indicators", country_payload)
    monkeypatch.setattr(comparison, "unified_events", events)


def row(payload, indicator_id):
    return next(item for item in payload["rows"] if item["id"] == indicator_id)


def test_v1191_year_mismatch_is_display_only_and_has_no_difference(monkeypatch):
    install(monkeypatch)
    payload = comparison.compare_indicators("KEN", "GHA")
    life = row(payload, "SP.DYN.LE00.IN")
    assert life["compatibility"] == "different-reporting-years"
    assert life["display_comparable"] is True
    assert life["calculation_eligible"] is False
    assert life["absolute_difference"] is None
    assert any("No mathematical difference" in message for message in life["warnings"])


def test_v1191_unit_and_source_conflicts_are_explicit(monkeypatch):
    install(monkeypatch)
    payload = comparison.compare_indicators("KEN", "GHA")
    unit = row(payload, "UNIT.TEST")
    source = row(payload, "SOURCE.TEST")
    assert unit["compatibility"] == "unit-conflict"
    assert unit["absolute_difference"] is None
    assert source["compatibility"] == "source-conflict"
    assert source["source_match"] is False
    assert source["absolute_difference"] is None
    assert payload["conflict_count"] >= 3


def test_v1191_world_bank_live_and_reference_snapshot_share_source_family(monkeypatch):
    install(monkeypatch)
    payload = comparison.compare_indicators("KEN", "GHA")
    population = row(payload, "SP.POP.TOTL")
    electricity = row(payload, "EG.ELC.ACCS.ZS")
    assert population["compatibility"] == "aligned"
    assert population["absolute_difference"] == -21.0
    assert electricity["availability"] == "comparison-only"
    assert electricity["compatibility"] == "partial"


def test_v1191_trend_gaps_and_chartability_are_retained(monkeypatch):
    install(monkeypatch)
    payload = comparison.compare_trends("KEN", "GHA")
    gap = next(item for item in payload["trends"] if item["id"] == "GAP.TEST")
    assert gap["chartable"] is True
    assert gap["common_years"] == [2022, 2023]
    assert gap["primary_gap_years"] == [2021]
    assert gap["comparison_gap_years"] == [2020]
    assert any(item["primary_missing"] for item in gap["aligned_series"])
    source = next(item for item in payload["trends"] if item["id"] == "SOURCE.TEST")
    assert source["chartable"] is False
    assert source["display_mode"] == "source-conflict"


def test_v1191_event_failure_stays_local(monkeypatch):
    install(monkeypatch)

    def failing_events(*, country_code: str, **kwargs):
        if country_code == "GHA":
            raise RuntimeError("upstream unavailable")
        return events(country_code=country_code, **kwargs)

    monkeypatch.setattr(comparison, "unified_events", failing_events)
    payload = comparison.compare_countries("KEN", "GHA", include_events=True, include_brief=True)
    assert payload["ok"] is True
    assert payload["summary"]["event_data_state"] == "partial"
    assert payload["events"]["comparison"]["data_state"] == "temporarily-unavailable"
    assert payload["brief"]["latest_available_indicators"]


def test_v1191_api_can_return_consistent_embedded_brief_and_diagnostics(monkeypatch):
    install(monkeypatch)
    client = TestClient(app)
    response = client.get("/public/compare?country=KEN&compare=GHA&include_brief=true")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "2.21.0"
    assert payload["brief"]["generated_at"] == payload["generated_at"]
    diagnostics = client.get("/public/compare/diagnostics?country=KEN&compare=GHA")
    assert diagnostics.status_code == 200
    assert diagnostics.json()["public_safe"] is True
    assert diagnostics.json()["issue_count"] >= 1


def test_v1191_strict_pair_and_indicator_validation(monkeypatch):
    install(monkeypatch)
    client = TestClient(app)
    assert client.get("/public/compare?country=K-E-N&compare=GHA").status_code == 404
    duplicate = client.get("/public/compare?country=KEN&compare=KEN")
    assert duplicate.status_code == 422
    unsupported = client.get("/public/compare/brief?country=KEN&compare=GHA&indicator=UNKNOWN")
    assert unsupported.status_code == 422


def test_v1191_exports_include_sources_states_warnings_and_safe_headers(monkeypatch):
    install(monkeypatch)
    csv_body, media_type, filename = comparison.comparison_export("KEN", "GHA", "csv")
    assert csv_body.startswith("\ufeff")
    assert media_type == "text/csv"
    assert filename.endswith(".csv")
    records = list(csv.DictReader(StringIO(csv_body.lstrip("\ufeff"))))
    life = next(item for item in records if item["indicator_id"] == "SP.DYN.LE00.IN")
    assert life["absolute_difference"] == ""
    assert life["primary_source_url"].startswith("https://")
    assert "No mathematical difference" in life["warnings"]
    html, html_type, _ = comparison.comparison_export("KEN", "GHA", "html")
    assert html_type == "text/html"
    assert "Methodological cautions" in html
    assert "data.worldbank.org" in html

    client = TestClient(app)
    response = client.get("/public/compare/export?country=KEN&compare=GHA&format=csv")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_v1191_public_app_mobile_print_share_and_plugin_contract():
    root = Path(__file__).resolve().parents[2]
    html = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    css = (root / "backend/public_app/assets/app.css").read_text(encoding="utf-8")
    php = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert 'id="compareValidation"' in html
    assert 'id="compareConflictCount"' in html
    assert 'id="compareTrendCount"' in html
    assert 'params.set("compareView",compareState.activeView)' in js
    assert 'include_brief:"true"' in js
    assert 'data-label="${escapeHtml(leftName)}"' in js
    assert '#compareBriefView,#compareBriefView[hidden]{display:block!important}' in css
    assert '.compare-table td::before{content:attr(data-label)' in css
    assert "Version: 2.21.0" in php
    assert "'view' => 'table'" in php
    assert "'indicator' => ''" in php
