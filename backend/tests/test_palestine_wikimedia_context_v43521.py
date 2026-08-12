from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

from app import authoritative_connectors_v43521 as connectors
from app import country_linked_records_v43520 as linked
from app import palestine_data_federation_v43521 as federation
from app import wikimedia_knowledge_context_v43521 as wikimedia


def test_palestine_open_data_connector_is_public_discovery_and_registered(monkeypatch):
    captured = {}
    monkeypatch.setattr(connectors, "_request_json", lambda url, timeout=8: captured.setdefault("url", url) or {"success": True})
    payload = connectors.palestine_open_data_search(None, query="water", rows=7)
    assert payload["connector_id"] == "palestine-open-data-ckan"
    assert payload["mode"] == "DISCOVERY"
    assert "official/public-institution dataset discovery" in payload["boundary"]
    query = parse_qs(urlsplit(captured["url"]).query)
    assert query["q"] == ["water"]
    assert query["rows"] == ["7"]
    catalog = connectors.connector_catalog(None)
    assert catalog["connector_count"] == 51
    assert any(row["id"] == "palestine-open-data-ckan" for row in catalog["connectors"])
    assert connectors.connector_readiness(None)["ok"] is True


def test_palestine_linked_records_include_official_portal_without_promoting_to_live(monkeypatch):
    settings = SimpleNamespace(external_request_timeout_seconds=1)
    monkeypatch.setattr(linked, "_country_identity", lambda code: (
        "PSE", {"name": "Palestine", "iso2": "PS", "aliases": ["Palestine", "State of Palestine"]},
    ))
    monkeypatch.setattr(linked, "unified_events", lambda **kwargs: {"events": [], "source_states": {"reliefweb": "unavailable"}})
    monkeypatch.setattr(linked, "palestine_open_data_search", lambda settings, query, rows: {
        "ok": True, "data": {"result": {"results": [{
            "id": "pod-1", "name": "water-resources", "title": "Water Resources",
            "notes": "Official public dataset.", "metadata_modified": "2026-08-10T00:00:00Z",
            "organization": {"title": "Palestinian Water Authority"},
        }]}}
    })
    monkeypatch.setattr(linked, "hdx_dataset_search", lambda settings, query, rows: {"ok": True, "data": {"result": {"results": []}}})
    payload = linked.build_country_linked_records(settings, country_code="PSE", limit=10)
    assert payload["count"] == 1
    row = payload["records"][0]
    assert row["record_class"] == "official-dataset-discovery"
    assert row["evidence_class"] == "official-discovery-metadata"
    assert row["data_state"] == "discovery"
    assert row["country_match_confidence"] == 1.0
    assert payload["source_states"]["palestine-open-data-ckan"] == "connected"


def test_palestine_federation_keeps_source_roles_separate(monkeypatch):
    monkeypatch.setattr(federation, "_country", lambda code: ("PSE", {"name": "Palestine"}))
    monkeypatch.setattr(federation, "palestine_open_data_search", lambda settings, query, rows: {"ok": True, "data": {"result": {"results": []}}})
    monkeypatch.setattr(federation, "hdx_dataset_search", lambda settings, query, rows: {"ok": True, "data": {"result": {"results": []}}})
    monkeypatch.setattr(federation, "hdx_hapi", lambda settings, **kwargs: {
        "ok": False, "configuration_required": True, "configuration_key": "SC_SI_HDX_HAPI_APP_IDENTIFIER"
    })
    payload = federation.build_palestine_data_federation(None, country_code="PSE")
    roles = {row["source_id"]: row["role"] for row in payload["source_precedence"]}
    assert roles["pcbs-pxweb"] == "PRIMARY OFFICIAL STATISTICS"
    assert roles["palestine-open-data-ckan"] == "OFFICIAL DATASET DISCOVERY"
    assert roles["hdx-hapi"] == "STANDARDIZED HUMANITARIAN INDICATORS"
    assert roles["world-bank"] == "HARMONIZED INTERNATIONAL COMPARISON"
    assert payload["source_states"]["hdx-hapi"] == "configuration-required"
    assert federation.readiness()["checks"]["wikimedia_excluded_from_truth_precedence"] is True


def test_wikidata_search_uses_mediawiki_action_api(monkeypatch):
    captured = {}
    def fake(url: str, timeout: int = 8):
        captured["url"] = url
        return {"search": [{"id": "Q219060", "label": "State of Palestine"}]}
    monkeypatch.setattr(wikimedia, "_request_json", fake)
    payload = wikimedia.wikidata_search(None, query="State of Palestine", language="en", limit=5)
    parsed = urlsplit(captured["url"])
    query = parse_qs(parsed.query)
    assert parsed.netloc == "www.wikidata.org"
    assert query["action"] == ["wbsearchentities"]
    assert query["search"] == ["State of Palestine"]
    assert payload["context_class"] == "LINKED KNOWLEDGE"


def test_commons_search_requests_machine_readable_license_metadata(monkeypatch):
    captured = {}
    def fake(url: str, timeout: int = 8):
        captured["url"] = url
        return {"query": {"pages": []}}
    monkeypatch.setattr(wikimedia, "_request_json", fake)
    payload = wikimedia.commons_media_search(None, query="Palestine geography", limit=4)
    query = parse_qs(urlsplit(captured["url"]).query)
    assert query["prop"] == ["imageinfo"]
    assert "extmetadata" in query["iiprop"][0]
    assert payload["context_class"] == "VISUAL KNOWLEDGE"
    assert "license" in payload["boundary"].lower()


def test_pageviews_is_explicitly_attention_not_severity(monkeypatch):
    captured = {}
    monkeypatch.setattr(wikimedia, "_request_json", lambda url, timeout=8: captured.setdefault("url", url) or {"items": []})
    payload = wikimedia.pageviews(None, article="State of Palestine", language="en", days=30)
    assert "/metrics/pageviews/per-article/en.wikipedia.org/all-access/user/" in captured["url"]
    assert payload["context_class"] == "PUBLIC ATTENTION SIGNAL"
    assert "do not measure event severity" in payload["boundary"]


def test_country_knowledge_context_composes_four_wikimedia_lanes(monkeypatch):
    monkeypatch.setattr(wikimedia, "_country", lambda code: ("PSE", {"name": "Palestine"}))
    monkeypatch.setattr(wikimedia, "wikidata_search", lambda *args, **kwargs: {"data": {"search": [{"id": "Q219060"}]}})
    monkeypatch.setattr(wikimedia, "wikidata_entity", lambda *args, **kwargs: {"data": {"entities": {"Q219060": {
        "labels": {"en": {"value": "State of Palestine"}},
        "descriptions": {"en": {"value": "country in Western Asia"}},
        "aliases": {"en": [{"value": "Palestine"}]},
        "sitelinks": {"enwiki": {"title": "State of Palestine"}},
    }}}})
    monkeypatch.setattr(wikimedia, "wikipedia_page_context", lambda *args, **kwargs: {"data": {"query": {"pages": [{
        "pageid": 1, "title": "State of Palestine", "extract": "Background text.", "fullurl": "https://en.wikipedia.org/wiki/State_of_Palestine"
    }]}}})
    monkeypatch.setattr(wikimedia, "commons_media_search", lambda *args, **kwargs: {"data": {"query": {"pages": [{
        "title": "File:Palestine map.svg", "imageinfo": [{"thumburl": "https://upload.wikimedia.org/example.svg", "descriptionurl": "https://commons.wikimedia.org/wiki/File:Palestine_map.svg", "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 4.0"}}}]
    }]}}})
    monkeypatch.setattr(wikimedia, "pageviews", lambda *args, **kwargs: {"data": {"items": [{"timestamp": "2026080100", "views": 100}, {"timestamp": "2026080200", "views": 150}]}})
    payload = wikimedia.country_knowledge_context(None, country_code="PSE", media_limit=4, pageview_days=30)
    assert payload["entity"]["id"] == "Q219060"
    assert payload["wikipedia"]["title"] == "State of Palestine"
    assert payload["media"][0]["license"] == "CC BY-SA 4.0"
    assert payload["attention"]["total"] == 250
    assert payload["truth_precedence"] == "excluded"
    assert all(payload["source_states"][k] == "connected" for k in ("wikidata", "wikipedia", "commons", "pageviews"))


def test_v43521_ui_and_readiness_contracts_are_wired():
    root = Path(__file__).resolve().parents[2]
    app_js = (root / "backend/public_app/assets/app.js").read_text()
    main = (root / "backend/app/main.py").read_text()
    assert "/knowledge-context?language=en&media_limit=4&pageview_days=30" in app_js
    assert "Wikimedia-linked context" in app_js
    assert "PALESTINE DATA FEDERATION" in app_js
    assert '@app.get("/public/country/{country_code}/knowledge-context")' in main
    assert '@app.get("/public/knowledge-context/readiness")' in main
    assert '@app.get("/public/country-data-federation/readiness")' in main
    ready = wikimedia.readiness()
    assert ready["ok"] is True
    assert ready["network_calls_performed"] is False
    assert ready["upstream_health_release_blocking"] is False
