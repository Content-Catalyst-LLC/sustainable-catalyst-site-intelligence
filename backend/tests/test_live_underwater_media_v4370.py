from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.live_underwater_media_v4370 import (
    provider_catalog,
    readiness,
    search,
    onc_image_request,
)
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
CLIENT = TestClient(app)


def settings(token=""):
    return SimpleNamespace(onc_api_token=token, underwater_media_timeout_seconds=7)


def test_provider_catalog_has_three_independent_lanes_and_onc_is_optional():
    payload = provider_catalog(settings())
    assert payload["ok"] is True
    assert payload["version"] == "4.37.0"
    assert payload["default_provider"] == "fathomnet"
    assert payload["provider_count"] == 3
    providers = {row["id"]: row for row in payload["providers"]}
    assert providers["fathomnet"]["configured"] is True
    assert providers["noaa-ocean-exploration"]["configured"] is True
    assert providers["onc-oceans-3"]["configuration_required"] is True
    assert providers["onc-oceans-3"]["credential"] == "SC_SI_ONC_API_TOKEN"


def test_readiness_is_network_free_and_missing_onc_token_does_not_block_release():
    payload = readiness(settings())
    assert payload["ok"] is True
    assert payload["network_calls_performed"] is False
    assert payload["release_blocking_upstream_health"] is False
    assert payload["provider_configuration"]["onc-oceans-3"] == "configuration-required"
    assert payload["checks"]["onc_missing_credential_non_blocking"] is True
    assert all(payload["checks"].values())


def test_fathomnet_live_query_returns_source_image_and_annotations_without_fabrication():
    calls = []
    def fake_json(url, **kwargs):
        calls.append(url)
        return [{
            "uuid": "fn-1",
            "url": "https://database.fathomnet.org/static/example.jpg",
            "latitude": 36.8,
            "longitude": -122.0,
            "depthMeters": 812.5,
            "timestamp": "2026-01-02T03:04:05Z",
            "boundingBoxes": [{"concept": "Octopus"}, {"concept": "Octopus"}],
            "observer": "FathomNet contributor",
        }]
    payload = search({"provider": "fathomnet", "query": "Octopus", "limit": 5}, settings(), request_json=fake_json)
    assert payload["ok"] is True and payload["record_count"] == 1
    assert "/images/query/concept/Octopus" in calls[0]
    row = payload["results"][0]
    assert row["record_type"] == "underwater-image"
    assert row["media_url"].startswith("https://database.fathomnet.org/")
    assert row["annotations"] == ["Octopus"]
    assert row["depth_m"] == 812.5
    assert payload["truth"]["visual_media_fabricated"] is False


def test_fathomnet_empty_query_uses_public_image_listing_instead_of_zero_zero_defaults():
    calls = []
    def fake_json(url, **kwargs):
        calls.append(url)
        return {"content": [{"id": 7, "url": "https://database.fathomnet.org/static/recent.jpg"}]}
    payload = search({"provider": "fathomnet", "limit": 3}, settings(), request_json=fake_json)
    assert payload["record_count"] == 1
    assert "/images/list/all" in calls[0]
    assert payload["query"]["latitude"] is None
    assert payload["query"]["longitude"] is None
    assert payload["query"]["depth_m"] is None


def test_onc_without_token_is_explicit_configuration_required_and_nonblocking():
    payload = search({"provider": "onc-oceans-3", "query": "Barkley"}, settings())
    assert payload["ok"] is True and payload["record_count"] == 0
    state = payload["provider_states"]["onc-oceans-3"]
    assert state["configuration_required"] is True
    assert state["configuration_key"] == "SC_SI_ONC_API_TOKEN"
    assert state["network_calls_performed"] is False


def test_onc_configured_lane_discovers_archive_and_proxies_images_without_token_exposure():
    calls = []
    def fake_json(url, **kwargs):
        calls.append(url)
        if "/locations?" in url:
            return [{"locationCode": "RISS", "lat": 48.4, "lon": -126.2, "depth": 950}]
        return {"files": [
            {"filename": "camera_20260816.jpg", "timestamp": "2026-08-16T10:00:00Z"},
            {"filename": "dive_clip.mp4", "timestamp": "2026-08-16T10:02:00Z"},
        ]}
    payload = search({"provider": "onc-oceans-3", "query": "Regional", "limit": 4}, settings("SECRET-TOKEN"), request_json=fake_json)
    assert payload["record_count"] == 2
    image, video = payload["results"]
    assert image["media_url"].startswith("/public/underwater-media/onc/file?")
    assert "SECRET-TOKEN" not in str(payload)
    assert video["record_type"] == "underwater-video" and video["media_url"] is None
    assert "[redacted]" in payload["provider_states"]["onc-oceans-3"]["endpoint"]
    assert any("deviceCategoryCode=VIDEOCAM" in url for url in calls)


def test_noaa_expedition_archive_discovers_direct_media_and_packages():
    def fake_text(url, **kwargs):
        assert url.endswith("ex2408/")
        return '<a href="images/deep_still.jpg">still</a><a href="video/dive01.mp4">video</a><a href="Underwater_Still_Images.zip">package</a>'
    payload = search({"provider": "noaa-ocean-exploration", "expedition_id": "EX2408", "limit": 5}, settings(), request_text=fake_text)
    assert payload["record_count"] == 3
    kinds = {row["record_type"] for row in payload["results"]}
    assert {"underwater-image", "underwater-video", "expedition-media-package"}.issubset(kinds)
    assert payload["provider_states"]["noaa-ocean-exploration"]["network_calls_performed"] is True


def test_bad_query_dimensions_are_rejected_without_network_calls():
    for request in (
        {"provider": "bogus"},
        {"provider": "fathomnet", "latitude": 4},
        {"provider": "fathomnet", "date_from": "2026-08-20", "date_to": "2026-08-10"},
        {"provider": "fathomnet", "depth_m": 12000},
    ):
        try:
            search(request, settings())
        except ValueError:
            pass
        else:
            raise AssertionError(request)


def test_onc_image_proxy_rejects_path_traversal_and_video_and_keeps_token_server_side():
    for name in ("../secret.jpg", "clip.mp4", "folder\\image.jpg"):
        try:
            onc_image_request(name, settings("SECRET"))
        except ValueError:
            pass
        else:
            raise AssertionError(name)
    url, headers = onc_image_request("camera_20260816.jpg", settings("SECRET"))
    assert "token=SECRET" in url
    assert headers["Accept"] == "image/*"


def test_public_readiness_and_provider_routes_are_live_without_onc_credential():
    providers = CLIENT.get("/public/underwater-media/providers")
    ready = CLIENT.get("/public/underwater-media/readiness")
    assert providers.status_code == 200 and ready.status_code == 200
    assert providers.json()["version"] == "4.37.0"
    assert ready.json()["ok"] is True
    old = CLIENT.get("/public/underwater-observation/readiness").json()
    assert old["checks"]["live_media_extension_ready"] is True
    assert old["summary"]["live_media_provider_count"] == 3


def test_frontend_is_live_media_first_and_has_no_fake_zero_zero_default():
    js = (ROOT / "backend/public_app/assets/underwater-observation-v4800.js").read_text()
    css = (ROOT / "backend/public_app/assets/underwater-observation-v4800.css").read_text()
    assert 'const VERSION="4.37.0"' in js
    assert "/public/underwater-media/search" in js
    assert "/public/underwater-media/providers" in js
    assert "Search live media" in js
    assert "fathomnet" in js and "SC_SI_ONC_API_TOKEN" in js
    assert "SC_SI_ONC_API_TOKEN" in js
    assert "underwater-video" in js and "uw4800-card" in css
    assert "value=\"0\"" not in js
    assert (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/underwater-observation-v4800.js").read_bytes() == (ROOT / "backend/public_app/assets/underwater-observation-v4800.js").read_bytes()
    assert (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/underwater-observation-v4800.css").read_bytes() == (ROOT / "backend/public_app/assets/underwater-observation-v4800.css").read_bytes()


def test_release_identity_is_v4370_and_ocean_inherits_live_underwater_readiness():
    assert CLIENT.get("/public/build-info").json()["version"] == "4.37.0"
    ocean = CLIENT.get("/public/ocean-observation/readiness").json()
    assert ocean["ok"] is True
    assert ocean["version"] == "4.37.0"
    assert ocean["systems"]["underwater"]["ok"] is True
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert "Version: 4.37.0" in plugin and "site-intelligence-v4.37.0" in plugin


def test_deployment_verification_requires_live_underwater_control_plane_but_not_onc_token():
    payload = CLIENT.get("/public/deployment-verification").json()
    assert payload["ok"] is True
    assert payload["contract"] == "deployment-verification-live-underwater-media-v4370"
    assert payload["checks"]["live_underwater_media_ready"] is True
    assert payload["checks"]["onc_underwater_credential_non_blocking"] is True
    assert "/public/underwater-media/readiness" in payload["required_routes"]
