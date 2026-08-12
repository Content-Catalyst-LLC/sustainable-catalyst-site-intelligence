from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from app import country_linked_records_v43520 as linked
from app import unified_live_events as events


def test_reliefweb_country_request_is_source_bounded(monkeypatch):
    captured = {}
    monkeypatch.setenv("SC_SI_RELIEFWEB_APPNAME", "site-intelligence-test-app")

    def fake_request(url: str, timeout: int = 10):
        captured["url"] = url
        return {"data": []}

    monkeypatch.setattr(events, "_request_json", fake_request)
    assert events._reliefweb_reports(days=30, limit=20, country_code="PSE") == []
    query = parse_qs(urlsplit(captured["url"]).query)
    assert query["filter[operator]"] == ["AND"]
    assert query["filter[conditions][1][field]"] == ["country.iso3"]
    assert query["filter[conditions][1][value]"] == ["PSE"]
    assert "filter[field]" not in query


def test_palestine_hdx_discovery_survives_missing_reliefweb(monkeypatch):
    monkeypatch.setattr(linked, "_country_identity", lambda code: (
        "PSE",
        {"name": "Palestine", "display_name": "Palestine", "iso2": "PS", "aliases": ["Palestine", "State of Palestine", "West Bank and Gaza"]},
    ))
    monkeypatch.setattr(linked, "unified_events", lambda **kwargs: {
        "events": [],
        "source_states": {"usgs": "live", "nasa-eonet": "live", "reliefweb": "unavailable"},
    })
    monkeypatch.setattr(linked, "hdx_dataset_search", lambda settings, query, rows: {
        "ok": True,
        "data": {"result": {"results": [{
            "id": "pse-water",
            "name": "state-of-palestine-water-data",
            "title": "State of Palestine: Water and WASH operational datasets",
            "notes": "Humanitarian datasets for Palestine.",
            "metadata_modified": "2026-08-11T12:00:00.000000",
            "organization": {"title": "OCHA oPt"},
            "groups": [{"name": "pse", "display_name": "State of Palestine"}],
        }]}}},
    )

    payload = linked.build_country_linked_records(None, country_code="PSE", days=90, limit=24)
    assert payload["ok"] is True
    assert payload["country"]["code"] == "PSE"
    assert payload["count"] == 1
    assert payload["dataset_discovery_count"] == 1
    row = payload["records"][0]
    assert row["record_class"] == "dataset-discovery"
    assert row["evidence_class"] == "discovery-metadata"
    assert row["country_match_method"] in {"hdx-explicit-iso3", "hdx-explicit-country-text"}
    assert row["source_url"].startswith("https://data.humdata.org/dataset/")
    assert "not a statement" in row["limitations"][0]


def test_country_linked_records_keeps_event_and_discovery_semantics_separate(monkeypatch):
    monkeypatch.setattr(linked, "_country_identity", lambda code: (
        "PSE", {"name": "Palestine", "iso2": "PS", "aliases": ["Palestine"]},
    ))
    monkeypatch.setattr(linked, "unified_events", lambda **kwargs: {
        "events": [{
            "id": "rw-1", "title": "Humanitarian update - Palestine", "summary": "Update",
            "category": "humanitarian", "category_label": "Humanitarian reports",
            "source": "reliefweb", "source_name": "ReliefWeb", "source_url": "https://reliefweb.int/report/example",
            "observed_at": "2026-08-12T00:00:00+00:00", "country_code": "PSE",
            "country_match_method": "source-country-field", "country_match_confidence": 0.99, "data_state": "live",
        }],
        "source_states": {"reliefweb": "live"},
    })
    monkeypatch.setattr(linked, "hdx_dataset_search", lambda settings, query, rows: {
        "ok": True,
        "data": {"result": {"results": [{
            "id": "hdx-1", "name": "palestine-dataset", "title": "Palestine humanitarian dataset",
            "metadata_modified": "2026-08-11T00:00:00+00:00", "groups": [{"display_name": "Palestine"}],
        }]}}},
    )
    payload = linked.build_country_linked_records(None, country_code="PSE", limit=10)
    classes = {row["record_class"] for row in payload["records"]}
    assert classes == {"event-or-report", "dataset-discovery"}
    assert payload["event_or_report_count"] == 1
    assert payload["dataset_discovery_count"] == 1


def test_country_workspace_uses_linked_record_contract():
    root = Path(__file__).resolve().parents[2]
    app_js = (root / "backend/public_app/assets/app.js").read_text()
    index = (root / "backend/public_app/index.html").read_text()
    main = (root / "backend/app/main.py").read_text()
    assert "/public/country/${encodeURIComponent(code)}/linked-records?days=90&limit=24" in app_js
    assert "No country-linked records" in app_js
    assert "Open humanitarian view" in index
    assert '@app.get("/public/country/{country_code}/linked-records")' in main
    country_loader = app_js[app_js.index("async function loadCountryEvents"):app_js.index("function setCountryLoading")]
    assert "/public/events?country_code=" not in country_loader
