from __future__ import annotations

import csv
from io import StringIO
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app import public_briefing_export_studio as studio


COUNTRY = {
    "code": "KEN",
    "iso2": "KE",
    "name": "Kenya",
    "region": "Sub-Saharan Africa",
    "capital": "Nairobi",
    "latitude": 0.0236,
    "longitude": 37.9062,
}


def country_profile(_code: str):
    return {
        "ok": True,
        "version": "3.9.0",
        "generated_at": "2026-07-11T00:00:00+00:00",
        "country": COUNTRY,
        "data_state": "partial-live",
        "summary": "Kenya country intelligence combines public indicators and event context.",
        "highlights": [],
        "interpretation": [
            "Values are descriptive public indicators and do not constitute a national ranking.",
            "Indicators may refer to different reporting years and methodologies.",
        ],
    }


def country_indicators(_code: str):
    return {
        "ok": True,
        "version": "3.9.0",
        "country": COUNTRY,
        "data_state": "partial-live",
        "indicators": [
            {
                "id": "SP.POP.TOTL",
                "key": "population",
                "label": "Population",
                "unit": "people",
                "format": "integer",
                "source": "World Bank Open Data",
                "source_id": "SP.POP.TOTL",
                "source_url": "https://data.worldbank.org/indicator/SP.POP.TOTL",
                "data_state": "live",
                "cache_state": "live",
                "retrieved_at": "2026-07-11T00:00:00+00:00",
                "stale": False,
                "latest": {"value": 55_000_000, "year": 2023},
                "series": [{"year": 2022, "value": 54_000_000}, {"year": 2023, "value": 55_000_000}],
            },
            {
                "id": "ZERO.TEST",
                "key": "zero_test",
                "label": "Zero remains valid",
                "unit": "index",
                "format": "decimal",
                "source": "World Bank Open Data",
                "source_id": "ZERO.TEST",
                "source_url": "https://data.worldbank.org/indicator/ZERO.TEST",
                "data_state": "live",
                "cache_state": "live",
                "retrieved_at": "2026-07-11T00:00:00+00:00",
                "stale": False,
                "latest": {"value": 0, "year": 2023},
                "series": [{"year": 2023, "value": 0}],
            },
            {
                "id": "MISSING.TEST",
                "key": "missing_test",
                "label": "Missing test",
                "unit": "%",
                "format": "percent",
                "source": "World Bank Open Data",
                "source_id": "MISSING.TEST",
                "source_url": "https://data.worldbank.org/indicator/MISSING.TEST",
                "data_state": "unavailable",
                "cache_state": "unavailable",
                "retrieved_at": None,
                "stale": False,
                "latest": None,
                "series": [],
            },
        ],
    }


def country_trends(_code: str):
    payload = country_indicators(_code)
    return {
        "ok": True,
        "version": "3.9.0",
        "country": COUNTRY,
        "data_state": "partial-live",
        "trends": [
            {
                "id": item["id"],
                "key": item["key"],
                "label": item["label"],
                "unit": item["unit"],
                "source": item["source"],
                "source_url": item["source_url"],
                "data_state": item["data_state"],
                "series": item["series"],
            }
            for item in payload["indicators"]
            if item["series"]
        ],
    }


def unified_events(**_kwargs):
    return {
        "ok": True,
        "version": "3.9.0",
        "data_state": "partial-live",
        "count": 1,
        "source_states": {"usgs": "live", "reliefweb": "unavailable"},
        "events": [
            {
                "id": "usgs-1",
                "title": "Public event",
                "category": "earthquake",
                "severity": "moderate",
                "country_code": "KEN",
                "observed_at": "2026-07-10T12:00:00+00:00",
                "source": "usgs",
                "source_name": "USGS Earthquake Hazards Program",
                "source_url": "https://earthquake.usgs.gov/earthquakes/eventpage/usgs-1",
                "data_state": "live",
                "coordinates": [37.0, 0.5],
                "country_match_method": "source-country-field",
                "country_match_confidence": 0.99,
            }
        ],
    }


def compare_countries(_country: str, _compare: str, **_kwargs):
    left = COUNTRY
    right = {**COUNTRY, "code": "GHA", "iso2": "GH", "name": "Ghana", "capital": "Accra", "longitude": -1.0232, "latitude": 7.9465}
    row = {
        "id": "SP.POP.TOTL",
        "label": "Population",
        "domain": "Human development",
        "unit": "people",
        "availability": "both",
        "compatibility": "different-reporting-years",
        "calculation_eligible": False,
        "absolute_difference": None,
        "percent_difference": None,
        "warnings": ["Reporting years differ: KEN 2023, GHA 2022. No mathematical difference is calculated."],
        "primary": {
            "value": 55_000_000,
            "year": 2023,
            "unit": "people",
            "source": "World Bank Open Data",
            "source_id": "SP.POP.TOTL",
            "source_url": "https://data.worldbank.org/indicator/SP.POP.TOTL",
            "data_state": "live",
        },
        "comparison": {
            "value": 34_000_000,
            "year": 2022,
            "unit": "people",
            "source": "World Bank Open Data",
            "source_id": "SP.POP.TOTL",
            "source_url": "https://data.worldbank.org/indicator/SP.POP.TOTL",
            "data_state": "live",
        },
    }
    events = {
        "primary": unified_events(),
        "comparison": {**unified_events(), "events": [], "count": 0, "data_state": "temporarily-unavailable"},
    }
    return {
        "ok": True,
        "version": "3.9.0",
        "generated_at": "2026-07-11T00:00:00+00:00",
        "scope": {"primary_country": left, "comparison_country": right},
        "summary": {"primary_event_count": 1, "comparison_event_count": 0},
        "indicators": {"rows": [row]},
        "trends": {"trends": [{"id": "SP.POP.TOTL", "label": "Population", "chartable": True}]},
        "events": events,
        "brief": {
            "title": "Kenya and Ghana — Comparative Intelligence Brief",
            "methodological_caveats": row["warnings"],
        },
        "boundaries": ["Comparison does not create a ranking."],
    }


def earth_manifest(*_args, **_kwargs):
    return {
        "ok": True,
        "version": "3.9.0",
        "title": "Sustainable Catalyst Earth Observation View",
        "view": {
            "layer_id": "true-color",
            "layer_title": "Corrected Reflectance True Color",
            "left_date": "2026-07-01",
            "right_date": "2026-07-10",
            "center": [0.5, 37.0],
            "zoom": 5,
            "opacity": 0.72,
        },
        "source": "NASA GIBS",
        "attribution": "NASA EOSDIS GIBS",
        "observation_type": "satellite imagery",
        "limits": "Cloud cover and compositing affect interpretation.",
        "comparison_boundary": "Apparent change may reflect processing or real-world change.",
    }


def dashboard_export(_dashboard_id: str, country: str = ""):
    return {
        "ok": True,
        "version": "3.9.0",
        "dashboard": {
            "ok": True,
            "dashboard_id": "climate-human-vulnerability",
            "title": "Climate and Human Vulnerability",
            "summary": "Cross-domain climate and human vulnerability context.",
            "domains": ["planetary-boundaries", "human-development"],
            "public_disclaimer": "Cross-domain views preserve source dates and uncertainty.",
        },
        "data": {
            "notes": ["Live values appear only when a connector returns a validated public record."],
            "evidence_items": [
                {
                    "domain": "planetary-boundaries",
                    "label": "Environmental pressure",
                    "data_state": "source-registry-ready",
                    "value_status": "No fabricated value; live value appears only when a connector returns a valid record.",
                }
            ],
        },
        "sources": {"sources": [{"source": "NASA POWER", "health": "registry-ready"}]},
        "brief": {
            "title": "Climate and Human Vulnerability — Source-Aware Brief",
            "summary": f"Thematic brief for {country or 'selected geography'}.",
            "sections": [{"heading": "Evidence boundary", "text": "Sources remain distinct."}],
        },
    }


def install(monkeypatch):
    monkeypatch.setattr(studio, "country_profile", country_profile)
    monkeypatch.setattr(studio, "country_indicators", country_indicators)
    monkeypatch.setattr(studio, "country_trends", country_trends)
    monkeypatch.setattr(studio, "unified_events", unified_events)
    monkeypatch.setattr(studio, "compare_countries", compare_countries)
    monkeypatch.setattr(studio, "earth_export_manifest", earth_manifest)
    monkeypatch.setattr(studio, "dashboard_export", dashboard_export)


def test_v1200_directory_and_diagnostics_are_public_safe():
    directory = studio.briefing_directory()
    diagnostics = studio.briefing_diagnostics()
    assert directory["version"] == "3.9.0"
    assert {item["id"] for item in directory["brief_types"]} == {"country", "comparison", "event", "earth", "thematic"}
    assert directory["server_export_formats"] == ["json", "csv", "html"]
    assert directory["browser_export_formats"] == ["png"]
    assert diagnostics["public_safe"] is True
    assert diagnostics["checks"]["pdf_export"] == "deferred"


def test_v1200_country_brief_preserves_zero_missing_data_and_sources(monkeypatch):
    install(monkeypatch)
    payload = studio.build_brief("country", country="KEN", days=14)
    records = payload["evidence"]["indicators"]
    zero = next(item for item in records if item["id"] == "ZERO.TEST")
    assert zero["value"] == 0
    assert payload["brief_id"].startswith("scb-")
    assert payload["scope"]["event_count"] == 1
    assert any(item["id"] == "MISSING.TEST" for item in payload["missing_data"])
    assert any(item["url"] and "worldbank.org" in item["url"] for item in payload["source_records"])
    assert payload["provenance"]["platform_core_state"] == "optional-not-required"


def test_v1200_country_event_failure_remains_local(monkeypatch):
    install(monkeypatch)
    monkeypatch.setattr(studio, "unified_events", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("offline")))
    payload = studio.build_brief("country", country="KEN")
    assert payload["ok"] is True
    assert payload["scope"]["event_count"] == 0
    assert payload["data_states"]["has_unavailable_data"] is True
    assert payload["evidence"]["indicators"]


def test_v1200_comparison_brief_retains_year_conflict_and_no_difference(monkeypatch):
    install(monkeypatch)
    payload = studio.build_brief("comparison", country="KEN", compare="GHA")
    assert payload["brief_type"] == "comparison"
    assert payload["scope"]["conflict_count"] == 1
    assert payload["missing_data"][0]["compatibility"] == "different-reporting-years"
    primary = payload["evidence"]["indicators"][0]
    assert primary["absolute_difference"] is None
    assert primary["calculation_eligible"] is False


def test_v1200_event_and_earth_and_thematic_brief_types(monkeypatch):
    install(monkeypatch)
    event = studio.build_brief("event", country="KEN", days=7)
    earth = studio.build_brief("earth", layer_id="true-color", date_a="2026-07-01", date_b="2026-07-10", latitude=0.5, longitude=37.0, zoom=5)
    thematic = studio.build_brief("thematic", dashboard_id="climate-human-vulnerability", country="KEN")
    assert event["scope"]["event_count"] == 1
    assert earth["evidence"]["layers"][0]["source"] == "NASA GIBS"
    assert earth["selected_dates"] == {"before": "2026-07-01", "after": "2026-07-10"}
    assert thematic["scope"]["domain_count"] == 2
    assert thematic["missing_data"][0]["record_type"] == "thematic-item"


def test_v1200_invalid_brief_inputs_are_explicit(monkeypatch):
    install(monkeypatch)
    with pytest.raises(ValueError, match="unsupported_brief_type"):
        studio.build_brief("unknown")
    with pytest.raises(ValueError, match="duplicate_country"):
        studio.build_brief("comparison", country="KEN", compare="KEN")
    with pytest.raises(ValueError, match="invalid_date_range"):
        studio.build_brief("earth", date_a="2026-07-10", date_b="2026-07-01")
    with pytest.raises(ValueError, match="unsupported_export_format"):
        studio.briefing_export("country", "pdf", country="KEN")


def test_v1200_json_csv_and_html_exports_are_source_complete(monkeypatch):
    install(monkeypatch)
    json_body, json_type, json_name = studio.briefing_export("country", "json", country="KEN")
    payload = json.loads(json_body)
    assert json_type == "application/json"
    assert json_name.endswith(".json")
    assert payload["export_manifest"]["schema_version"] == "sc-public-briefing/1.0"
    assert payload["source_records"]

    csv_body, csv_type, csv_name = studio.briefing_export("country", "csv", country="KEN")
    assert csv_body.startswith("\ufeff")
    assert csv_type == "text/csv"
    assert csv_name.endswith(".csv")
    rows = list(csv.DictReader(StringIO(csv_body.lstrip("\ufeff"))))
    zero = next(item for item in rows if item["id"] == "ZERO.TEST")
    assert zero["value"] == "0"
    assert zero["source_url"].startswith("https://")

    html, html_type, html_name = studio.briefing_export("country", "html", country="KEN")
    assert html_type == "text/html"
    assert html_name.endswith(".html")
    assert "Responsible-use boundary" in html
    assert "data.worldbank.org" in html
    assert "No validated public value" in html


def test_v1200_api_endpoints_and_export_headers(monkeypatch):
    install(monkeypatch)
    client = TestClient(app)
    directory = client.get("/public/briefing-studio")
    assert directory.status_code == 200
    brief = client.get("/public/briefing-studio/brief?type=country&country=KEN")
    assert brief.status_code == 200
    assert brief.json()["version"] == "3.9.0"
    export = client.get("/public/briefing-studio/export?type=country&country=KEN&format=csv")
    assert export.status_code == 200
    assert export.headers["cache-control"] == "no-store"
    assert export.headers["x-content-type-options"] == "nosniff"
    assert "attachment" in export.headers["content-disposition"]
    duplicate = client.get("/public/briefing-studio/brief?type=comparison&country=KEN&compare=KEN")
    assert duplicate.status_code == 422


def test_v1200_public_app_and_wordpress_contract():
    root = Path(__file__).resolve().parents[2]
    html = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    css = (root / "backend/public_app/assets/app.css").read_text(encoding="utf-8")
    php = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert 'data-route="briefing"' in html
    assert 'id="briefingStudio"' in html
    assert 'data-briefing-export="png"' in html
    assert '/public/briefing-studio/brief?' in js
    assert 'html2canvas(qs("#briefingCapture")' in js
    assert 'body.briefing-print-mode' in css
    assert "add_shortcode('sc_public_briefing_studio'" in php
    assert "public function public_briefing_studio_shortcode" in php
    assert "Version: 3.9.0" in php
    assert "const VERSION = '3.9.0';" in php
