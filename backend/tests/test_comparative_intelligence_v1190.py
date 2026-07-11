from __future__ import annotations

from fastapi.testclient import TestClient

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
}


def _indicator(indicator_id: str, key: str, label: str, value: float | None, year: int | None, unit: str, state: str = "live"):
    latest = None if value is None else {"value": value, "year": year}
    return {
        "id": indicator_id,
        "key": key,
        "label": label,
        "domain": "Test domain",
        "unit": unit,
        "format": "decimal",
        "source": "World Bank",
        "source_id": indicator_id,
        "source_url": f"https://example.test/{indicator_id}",
        "data_state": state if latest else "unavailable",
        "cache_state": state,
        "retrieved_at": "2026-07-10T00:00:00+00:00",
        "stale": state == "stale",
        "latest": latest,
        "series": [] if latest is None else [
            {"year": year - 1, "value": value - 1},
            {"year": year, "value": value},
        ],
    }


def _country_payload(code: str):
    if code == "KEN":
        indicators = [
            _indicator("SP.POP.TOTL", "population", "Population", 55.0, 2023, "people"),
            _indicator("SP.DYN.LE00.IN", "life_expectancy", "Life expectancy", 66.7, 2022, "years"),
            _indicator("EG.ELC.ACCS.ZS", "electricity_access", "Electricity access", None, None, "% of population"),
        ]
    else:
        indicators = [
            _indicator("SP.POP.TOTL", "population", "Population", 34.0, 2023, "people"),
            _indicator("SP.DYN.LE00.IN", "life_expectancy", "Life expectancy", 64.5, 2021, "years"),
            _indicator("EG.ELC.ACCS.ZS", "electricity_access", "Electricity access", 89.5, 2022, "% of population", "reference-snapshot"),
        ]
    return {
        "ok": True,
        "version": "1.25.0",
        "country": COUNTRIES[code],
        "data_state": "live",
        "indicators": indicators,
    }


def _trend_payload(code: str):
    payload = _country_payload(code)
    return {
        "ok": True,
        "version": "1.25.0",
        "country": payload["country"],
        "data_state": "live",
        "trends": [
            {
                "id": item["id"],
                "key": item["key"],
                "label": item["label"],
                "unit": item["unit"],
                "format": item["format"],
                "series": item["series"],
            }
            for item in payload["indicators"]
            if item["series"]
        ],
    }


def _events(*, country_code: str, **_kwargs):
    count = 2 if country_code == "KEN" else 1
    return {
        "ok": True,
        "version": "1.25.0",
        "data_state": "live",
        "count": count,
        "events": [
            {
                "id": f"{country_code}-{index}",
                "title": f"Event {index}",
                "country_code": country_code,
                "source_name": "Public source",
            }
            for index in range(count)
        ],
    }


def _install_fixtures(monkeypatch):
    monkeypatch.setattr(comparison, "country_catalog", lambda: {"countries": list(COUNTRIES.values())})
    monkeypatch.setattr(comparison, "country_indicators", _country_payload)
    monkeypatch.setattr(comparison, "country_trends", _trend_payload)
    monkeypatch.setattr(comparison, "unified_events", _events)


def test_v1190_indicator_comparison_keeps_years_units_and_missing_values(monkeypatch):
    _install_fixtures(monkeypatch)
    payload = comparison.compare_indicators("KEN", "GHA")
    assert payload["version"] == "1.25.0"
    assert payload["indicator_count"] == 3
    population = next(row for row in payload["rows"] if row["id"] == "SP.POP.TOTL")
    assert population["compatibility"] == "aligned"
    assert population["absolute_difference"] == -21.0
    life = next(row for row in payload["rows"] if row["id"] == "SP.DYN.LE00.IN")
    assert life["compatibility"] == "different-reporting-years"
    assert any("Reporting years differ" in item for item in life["warnings"])
    electricity = next(row for row in payload["rows"] if row["id"] == "EG.ELC.ACCS.ZS")
    assert electricity["compatibility"] == "partial"
    assert electricity["primary"] is None
    assert electricity["comparison"]["data_state"] == "reference-snapshot"


def test_v1190_duplicate_country_is_rejected(monkeypatch):
    _install_fixtures(monkeypatch)
    client = TestClient(app)
    response = client.get("/public/compare?country=KEN&compare=KEN")
    assert response.status_code == 422
    assert response.json()["detail"] == "duplicate_country"


def test_v1190_comparison_endpoint_returns_summary_trends_and_events(monkeypatch):
    _install_fixtures(monkeypatch)
    client = TestClient(app)
    response = client.get("/public/compare?country=KEN&compare=GHA")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "1.25.0"
    assert payload["summary"]["indicator_count"] == 3
    assert payload["summary"]["primary_event_count"] == 2
    assert payload["summary"]["comparison_event_count"] == 1
    assert payload["routes"]["brief"].startswith("/public/compare/brief")


def test_v1190_trends_preserve_country_series(monkeypatch):
    _install_fixtures(monkeypatch)
    payload = comparison.compare_trends("KEN", "GHA")
    population = next(item for item in payload["trends"] if item["id"] == "SP.POP.TOTL")
    assert len(population["primary_series"]) == 2
    assert len(population["comparison_series"]) == 2
    assert population["common_year_count"] == 2


def test_v1190_brief_contains_sources_and_methodological_caveats(monkeypatch):
    _install_fixtures(monkeypatch)
    payload = comparison.comparison_brief("KEN", "GHA")
    assert payload["title"].startswith("Kenya and Ghana")
    assert payload["source_list"]
    assert any("Reporting years differ" in item for item in payload["methodological_caveats"])
    assert "Verify consequential findings" in payload["boundary"]


def test_v1190_export_supports_json_csv_and_html(monkeypatch):
    _install_fixtures(monkeypatch)
    for export_format, media_type, suffix in [
        ("json", "application/json", ".json"),
        ("csv", "text/csv", ".csv"),
        ("html", "text/html", ".html"),
    ]:
        body, returned_media_type, filename = comparison.comparison_export("KEN", "GHA", export_format)
        assert body
        assert returned_media_type == media_type
        assert filename.endswith(suffix)


def test_v1190_public_app_and_wordpress_plugin_expose_comparison_studio():
    root = __import__("pathlib").Path(__file__).resolve().parents[2]
    html = (root / "backend" / "public_app" / "index.html").read_text(encoding="utf-8")
    js = (root / "backend" / "public_app" / "assets" / "app.js").read_text(encoding="utf-8")
    php = (root / "wordpress-plugin" / "sustainable-catalyst-site-intelligence" / "sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert 'id="compareStudio"' in html
    assert "/public/compare?" in js
    assert "sc_comparative_intelligence" in php
    assert "Version: 1.25.0" in php
