from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.live_intelligence_analytics_v372 import sanitize_analytics_event
from app.live_intelligence_gateway_v370 import apply_gateway_policy
from app.live_intelligence_surfaces_v380 import (
    EMBED_MANIFEST_SCHEMA_VERSION,
    SURFACE_SCHEMA_VERSION,
    apply_connected_surface_policy,
    embed_manifest,
    normalize_surface_id,
    surface_definition,
    surface_directory,
    surface_policy,
)


def sample_signal(signal_id="event.surface.1", family="climate_earth_systems"):
    now = datetime.now(timezone.utc).isoformat()
    return {
        "signal_id": signal_id,
        "category": "earth_systems" if family == "climate_earth_systems" else "research",
        "feed_id": "usgs_earthquakes" if family == "climate_earth_systems" else "openalex",
        "label": "PUBLIC SIGNAL",
        "value": "Source-aware observation",
        "source_name": "Public source",
        "source_url": "https://example.org/source",
        "destination_url": "/platform/site-intelligence/",
        "context_view_url": f"/public/live-intelligence/signals/{signal_id}/view",
        "evidence_url": f"/public/live-intelligence/signals/{signal_id}/evidence",
        "observed_at": now,
        "updated_at": now,
        "validation_state": "valid",
        "selection_score": 200,
        "signal_family": family,
    }


def gateway_payload(*signals):
    return apply_gateway_policy({"ok": True, "signals": list(signals), "display": {}, "boundaries": []}, surface="homepage")


def test_surface_directory_exposes_eight_governed_surfaces():
    payload = surface_directory()
    assert payload["schema"] == SURFACE_SCHEMA_VERSION
    assert payload["count"] == 8
    ids = [item["surface_id"] for item in payload["surfaces"]]
    assert ids == ["homepage", "static_strip", "channel", "publication", "library", "advisory", "lab", "external_embed"]
    assert payload["governance"]["separate_ingestion_per_surface"] is False
    assert payload["governance"]["advertising_or_affiliate_signals"] is False


def test_surface_aliases_and_embed_contract_are_bounded():
    assert normalize_surface_id("research-library") == "library"
    manifest = embed_manifest("external_embed")
    assert manifest["schema"] == EMBED_MANIFEST_SCHEMA_VERSION
    assert manifest["security"]["api_credentials_in_browser"] is False
    assert manifest["security"]["administrative_routes_exposed"] is False
    try:
        embed_manifest("homepage")
        assert False, "homepage must not be approved as an external embed"
    except ValueError:
        pass


def test_publication_surface_filters_families_and_destinations():
    payload = gateway_payload(
        sample_signal("event.climate", "climate_earth_systems"),
        sample_signal("event.research", "science_environment"),
    )
    result = apply_connected_surface_policy(payload, "publication", limit=5)
    assert result["count"] == 1
    signal = result["signals"][0]
    assert signal["signal_id"] == "event.research"
    assert signal["surface_id"] == "publication"
    destination_types = {signal["primary_destination"]["type"]}
    destination_types.update(item["type"] for item in signal["secondary_destinations"])
    assert "decision_studio" not in destination_types
    assert "map_context" not in destination_types


def test_external_embed_preserves_source_and_freshness_contracts():
    payload = gateway_payload(sample_signal())
    payload["signals"][0]["freshness_state"] = "recently_updated"
    result = apply_connected_surface_policy(payload, "external_embed", limit=6)
    signal = result["signals"][0]
    assert signal["freshness_state"] == "recently_updated"
    assert signal["source_url"] == "https://example.org/source"
    assert signal["embed_safe"] is True
    assert signal["surface_presentation"] == "static"
    types = {signal["primary_destination"]["type"]}
    types.update(item["type"] for item in signal["secondary_destinations"])
    assert "decision_studio" not in types


def test_surface_policy_discloses_canonical_contracts_and_boundaries():
    policy = surface_policy()
    assert policy["version"] == "3.11.0"
    assert policy["canonical_contracts"]["freshness_status"] == "/public/live-intelligence/status"
    assert any("may not rewrite" in item for item in policy["boundaries"])
    assert any("Advertising" in item for item in policy["boundaries"])


def test_surface_analytics_dimensions_are_accepted_without_identifiers():
    clean = sanitize_analytics_event({
        "event_type": "component_impression", "surface": "library",
        "viewport": "desktop", "motion_mode": "manual", "delivery_state": "live",
        "destination_type": "signal_context", "signal_family": "science_environment",
        "freshness_state": "live", "source_id": "openalex",
    })
    assert clean["surface"] == "library"


def test_surface_directory_definition_and_embed_endpoints():
    client = TestClient(main.app)
    directory = client.get("/public/live-intelligence/surfaces")
    definition = client.get("/public/live-intelligence/surfaces/lab")
    policy = client.get("/public/live-intelligence/surface-policy")
    embed = client.get("/public/live-intelligence/embed-manifest?surface=external_embed")
    missing = client.get("/public/live-intelligence/surfaces/not-real")
    assert directory.status_code == 200 and directory.json()["count"] == 8
    assert definition.status_code == 200 and definition.json()["surface_id"] == "lab"
    assert policy.status_code == 200
    assert embed.status_code == 200 and embed.json()["surface"]["surface_id"] == "external_embed"
    assert missing.status_code == 404


def test_surface_feed_endpoint_reuses_gateway_and_rotation(monkeypatch, tmp_path):
    settings = Settings(
        live_intelligence_rotation_state_path=str(tmp_path / "rotation.json"),
        live_intelligence_analytics_state_path=str(tmp_path / "analytics.json"),
    )
    monkeypatch.setattr(main, "build_live_intelligence", lambda *args, **kwargs: {
        "ok": True, "version": "3.11.0", "signals": [sample_signal("event.research", "science_environment")],
        "display": {}, "boundaries": [],
    })
    monkeypatch.setattr(main, "apply_live_intelligence_rotation_policy", lambda payload, *args, **kwargs: payload)
    main.app.dependency_overrides[main.get_settings] = lambda: settings
    try:
        response = TestClient(main.app).get("/public/live-intelligence/surfaces/library/feed?limit=4")
    finally:
        main.app.dependency_overrides.pop(main.get_settings, None)
    assert response.status_code == 200
    payload = response.json()
    assert payload["surface"]["surface_id"] == "library"
    assert payload["signals"][0]["surface_id"] == "library"
    assert payload["measurement"]["individual_user_tracking"] is False
