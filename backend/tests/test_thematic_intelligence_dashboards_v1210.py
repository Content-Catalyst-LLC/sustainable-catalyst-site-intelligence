from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app import thematic_intelligence_dashboards as thematic


COUNTRY = {
    "code": "KEN",
    "iso2": "KE",
    "name": "Kenya",
    "region": "Sub-Saharan Africa",
    "capital": "Nairobi",
    "latitude": 0.0236,
    "longitude": 37.9062,
}

INDICATORS = {
    "SP.POP.TOTL": ("Population", "people", 55_000_000, "2023", "integer", "Population"),
    "SP.DYN.LE00.IN": ("Life expectancy", "years", 66.7, "2022", "decimal", "Health"),
    "NY.GDP.PCAP.CD": ("GDP per capita", "current US$", 2200.0, "2023", "currency", "Economy"),
    "EG.ELC.ACCS.ZS": ("Access to electricity", "% of population", 76.5, "2022", "percent", "Infrastructure"),
    "SH.H2O.BASW.ZS": ("Basic drinking water", "% of population", 64.0, "2022", "percent", "Water"),
    "SE.SEC.ENRR": ("Secondary enrollment", "% gross", 72.0, "2021", "percent", "Education"),
    "EN.ATM.CO2E.PC": ("CO₂ emissions per capita", "metric tons per capita", 0.4, "2020", "decimal", "Environment"),
    "SI.POV.GINI": ("Gini index", "index", None, None, "decimal", "Inequality"),
}


def fake_country_indicators(_code: str):
    rows = []
    for indicator_id, (label, unit, value, year, fmt, domain) in INDICATORS.items():
        rows.append({
            "id": indicator_id,
            "key": indicator_id.lower().replace(".", "_"),
            "label": label,
            "domain": domain,
            "unit": unit,
            "format": fmt,
            "source": "World Bank Open Data",
            "source_id": indicator_id,
            "source_url": f"https://data.worldbank.org/indicator/{indicator_id}",
            "data_state": "live" if value is not None else "unavailable",
            "cache_state": "live" if value is not None else "unavailable",
            "retrieved_at": "2026-07-11T12:00:00+00:00" if value is not None else None,
            "stale": False,
            "latest": {"value": value, "year": year} if value is not None else None,
        })
    return {
        "ok": True,
        "version": "3.8.0",
        "country": COUNTRY,
        "data_state": "partial-live",
        "indicators": rows,
    }


def fake_country_trends(_code: str):
    rows = []
    for indicator_id, (label, unit, value, year, _fmt, _domain) in INDICATORS.items():
        if value is None:
            continue
        current_year = int(year)
        rows.append({
            "id": indicator_id,
            "key": indicator_id.lower().replace(".", "_"),
            "label": label,
            "unit": unit,
            "source": "World Bank Open Data",
            "source_url": f"https://data.worldbank.org/indicator/{indicator_id}",
            "data_state": "live",
            "stale": False,
            "series": [
                {"year": current_year - 2, "value": float(value) * 0.96},
                {"year": current_year, "value": value},
            ],
        })
    return {
        "ok": True,
        "version": "3.8.0",
        "country": COUNTRY,
        "data_state": "partial-live",
        "trends": rows,
    }


def fake_layers():
    ids = [
        "true-color",
        "land-surface-temperature",
        "precipitation-rate",
        "vegetation-index",
        "fires-thermal-anomalies",
        "aerosol-optical-depth",
        "nighttime-lights",
    ]
    return {
        "ok": True,
        "version": "3.8.0",
        "layers": [
            {
                "id": item,
                "title": item.replace("-", " ").title(),
                "description": f"Public {item} context.",
                "source": "NASA GIBS",
                "attribution": "NASA EOSDIS GIBS",
                "temporal_resolution": "daily",
                "spatial_resolution": "varies by product",
                "observation_type": "satellite-derived" if item != "true-color" else "satellite imagery",
                "status": "public-beta",
                "limits": "Resolution, latency, cloud conditions, and processing affect interpretation.",
            }
            for item in ids
        ],
    }


def fake_events(**_kwargs):
    event = {
        "id": "eonet-1",
        "title": "Public environmental event",
        "summary": "Source-aware public event record.",
        "category": "wildfire",
        "category_label": "Wildfire",
        "severity": "moderate",
        "observed_at": "2026-07-10T12:00:00+00:00",
        "source": "nasa-eonet",
        "source_name": "NASA EONET",
        "source_url": "https://eonet.gsfc.nasa.gov/",
        "data_state": "live",
        "coordinates": [37.0, 0.5],
        "country_code": "KEN",
        "country_match_method": "source-country-field",
        "country_match_confidence": 0.99,
    }
    return {
        "ok": True,
        "version": "3.8.0",
        "generated_at": "2026-07-11T12:00:00+00:00",
        "data_state": "live",
        "delivery_state": "live",
        "source_states": {"nasa-eonet": "live", "usgs": "live", "reliefweb": "cached"},
        "count": 1,
        "events": [event],
        "geojson": {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [37.0, 0.5]}, "properties": {"id": event["id"], "title": event["title"]}}],
        },
    }


def install(monkeypatch):
    monkeypatch.setattr(thematic, "country_indicators", fake_country_indicators)
    monkeypatch.setattr(thematic, "country_trends", fake_country_trends)
    monkeypatch.setattr(thematic, "earth_layers", fake_layers)
    monkeypatch.setattr(thematic, "unified_events", fake_events)


def test_directory_registers_four_public_beta_dashboards():
    payload = thematic.dashboard_directory()
    assert payload["version"] == "3.8.0"
    assert payload["dashboard_count"] == 4
    assert {item["id"] for item in payload["dashboards"]} == {
        "climate-environment",
        "human-development",
        "human-security",
        "infrastructure",
    }
    assert all(item["maturity"] == "Public beta" for item in payload["dashboards"])


@pytest.mark.parametrize("dashboard_id", [
    "climate-environment",
    "human-development",
    "human-security",
    "infrastructure",
])
def test_each_dashboard_has_indicators_map_sources_methods_and_exports(monkeypatch, dashboard_id):
    install(monkeypatch)
    payload = thematic.build_dashboard(dashboard_id, "KEN", days=30)
    assert payload["ok"] is True
    assert payload["version"] == "3.8.0"
    assert payload["schema_version"] == "sc-thematic-dashboard/1.0"
    assert payload["dashboard"]["maturity"] == "Public beta"
    assert payload["country"]["code"] == "KEN"
    assert len(payload["indicators"]) >= 3
    assert payload["summary"]["available_indicator_count"] >= 3
    assert payload["summary"]["layer_count"] >= 3
    assert payload["summary"]["source_count"] >= 2
    assert payload["events"]["count"] == 1
    assert payload["map"]["latitude"] == COUNTRY["latitude"]
    assert payload["methodology"]
    assert payload["interpretation_limits"]
    assert "json" in thematic.ALLOWED_EXPORT_FORMATS


def test_missing_indicator_and_event_failure_stay_local(monkeypatch):
    install(monkeypatch)

    def failed_events(**_kwargs):
        raise TimeoutError("optional feed timeout")

    monkeypatch.setattr(thematic, "unified_events", failed_events)
    payload = thematic.build_dashboard("human-development", "KEN", days=30)
    assert payload["summary"]["available_indicator_count"] >= 3
    assert payload["events"]["data_state"] == "temporarily-unavailable"
    assert any(item["id"] == "SI.POV.GINI" for item in payload["missing_data"])
    assert any(item["id"] == "event-context" for item in payload["missing_data"])
    assert payload["data_state"] == "partial-live"


def test_trend_gaps_are_explicit_and_not_interpolated(monkeypatch):
    install(monkeypatch)
    payload = thematic.dashboard_trends("climate-environment", "KEN")
    assert payload["trends"]
    assert all(item["chartable"] is True for item in payload["trends"])
    assert all(item["point_count"] == 2 for item in payload["trends"])
    assert any(item["gap_years"] for item in payload["trends"])


def test_public_endpoints_and_diagnostics(monkeypatch):
    install(monkeypatch)
    client = TestClient(app)
    directory = client.get("/public/thematic-dashboards")
    dashboard = client.get("/public/thematic-dashboard/climate-environment?country=KEN&days=30")
    diagnostics = client.get("/public/thematic-dashboard/climate-environment/diagnostics?country=KEN&days=30")
    brief = client.get("/public/thematic-dashboard/climate-environment/brief?country=KEN&days=30")
    assert directory.status_code == 200
    assert dashboard.status_code == 200
    assert diagnostics.status_code == 200
    assert brief.status_code == 200
    assert dashboard.json()["dashboard"]["id"] == "climate-environment"
    assert diagnostics.json()["public_safe"] is True
    assert brief.json()["evidence"]["indicators"]


def test_exports_preserve_sources_states_and_safe_headers(monkeypatch):
    install(monkeypatch)
    client = TestClient(app)
    json_response = client.get("/public/thematic-dashboard/human-security/export?country=KEN&format=json")
    csv_response = client.get("/public/thematic-dashboard/human-security/export?country=KEN&format=csv")
    html_response = client.get("/public/thematic-dashboard/human-security/export?country=KEN&format=html")
    assert json_response.status_code == csv_response.status_code == html_response.status_code == 200
    assert json_response.headers["cache-control"] == "no-store"
    assert json_response.headers["x-content-type-options"] == "nosniff"
    assert json_response.json()["sources"]
    rows = list(csv.DictReader(StringIO(csv_response.content.decode("utf-8-sig"))))
    assert rows
    assert {row["record_type"] for row in rows} >= {"indicator", "event", "earth-layer"}
    assert all("source_url" in row for row in rows)
    assert "Responsible-use boundary" in html_response.text
    assert "NASA EONET" in html_response.text


def test_thematic_briefing_uses_canonical_investigation_manifest(monkeypatch):
    install(monkeypatch)
    client = TestClient(app)
    response = client.get("/public/briefing-studio/brief?type=thematic&dashboard_id=climate-environment&country=KEN")
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "sc-public-briefing/1.0"
    assert payload["brief_type"] == "thematic"
    assert payload["evidence"]["indicators"]
    assert payload["evidence"]["layers"]
    assert payload["source_records"]


def test_invalid_dashboard_and_export_format_are_explicit(monkeypatch):
    install(monkeypatch)
    client = TestClient(app)
    assert client.get("/public/thematic-dashboard/not-real?country=KEN").status_code == 404
    response = client.get("/public/thematic-dashboard/climate-environment/export?country=KEN&format=pdf")
    assert response.status_code == 422
    assert response.json()["detail"] == "unsupported_export_format"


def test_frontend_and_wordpress_expose_thematic_product():
    repository = Path(__file__).resolve().parents[2]
    html = (repository / "backend/public_app/index.html").read_text(encoding="utf-8")
    js = (repository / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    css = (repository / "backend/public_app/assets/app.css").read_text(encoding="utf-8")
    php = (repository / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert 'data-route="thematic"' in html
    assert 'id="thematicStudio"' in html
    assert 'openThematicStudio' in js
    assert 'AbortController' in js
    assert '.thematic-studio' in css
    assert "add_shortcode('sc_thematic_intelligence'" in php
    assert 'public function thematic_intelligence_shortcode' in php
    assert "Version: 3.8.0" in php
    assert "const VERSION = '3.8.0';" in php
