from fastapi.testclient import TestClient
import pytest

from app import main
from app.config import Settings
from app.live_intelligence_channels_v350 import (
    CHANNEL_REGISTRY,
    build_live_intelligence,
    channel_definition,
    channel_directory,
    channel_policy,
    filter_channel_signals,
)


def sample_signals():
    return [
        {"signal_id": "weather.us", "category": "earth_systems", "feed_id": "noaa_nws", "label": "WEATHER ALERT", "value": "Storm warning", "detail": "Severe weather in Illinois", "country": "United States", "country_code": "US", "region": "North America"},
        {"signal_id": "quake.jp", "category": "earth_systems", "feed_id": "usgs_earthquakes", "label": "EARTHQUAKE", "value": "M5.1 near Tokyo", "detail": "Earthquake record", "country": "Japan", "country_code": "JP", "region": "Asia"},
        {"signal_id": "human.ke", "category": "human_systems", "feed_id": "reliefweb", "label": "HUMANITARIAN REPORT", "value": "Flood response update", "detail": "Kenya humanitarian report", "country": "Kenya", "country_code": "KE", "region": "Africa"},
        {"signal_id": "research.grid", "category": "research", "feed_id": "openalex", "label": "OPEN RESEARCH", "value": "Power-grid resilience", "detail": "Infrastructure resilience research", "country": "", "country_code": "", "region": ""},
        {"signal_id": "economy.global", "category": "economy_resources", "feed_id": "world_bank", "label": "RENEWABLE ENERGY", "value": "Global indicator", "detail": "Data year 2024", "country": "", "country_code": "", "region": "Global"},
    ]


def sample_base(*args, **kwargs):
    return {
        "ok": True,
        "version": "3.16.0",
        "schema": "sc-site-intelligence-live-intelligence/1.4",
        "generated_at": "2026-07-21T00:00:00+00:00",
        "category": "all",
        "count": len(sample_signals()),
        "signals": sample_signals(),
        "feeds": [],
        "feed_state": {"useful_signal_count": 5, "platform_signal_count": 0},
        "source_operations": {"enabled": False},
        "display": {},
        "boundaries": [],
    }


def test_channel_directory_and_policy_are_public_and_explicit():
    directory = channel_directory()
    assert directory["version"] == "3.16.0"
    assert directory["count"] == len(CHANNEL_REGISTRY)
    assert any(item["id"] == "weather-climate" for item in directory["channels"])
    assert channel_definition("mena")["channel"]["id"] == "middle-east-north-africa"
    policy = channel_policy()
    assert any("empty" in item.lower() for item in policy["capabilities"])
    assert any("does not infer location" in item for item in policy["non_claims"])


def test_topic_region_and_country_filters_are_explicit():
    weather, weather_meta = filter_channel_signals(sample_signals(), channel_id="weather-climate")
    assert [item["signal_id"] for item in weather] == ["weather.us"]
    assert weather_meta["silent_global_fallback"] is False

    africa, _ = filter_channel_signals(sample_signals(), channel_id="africa")
    assert [item["signal_id"] for item in africa] == ["human.ke"]

    japan, _ = filter_channel_signals(sample_signals(), channel_id="global", country="JP")
    assert [item["signal_id"] for item in japan] == ["quake.jp"]

    resilience, _ = filter_channel_signals(sample_signals(), channel_id="infrastructure-resilience")
    assert [item["signal_id"] for item in resilience] == ["research.grid", "economy.global"]


def test_empty_geographic_match_does_not_fall_back_to_global():
    filtered, meta = filter_channel_signals(sample_signals(), channel_id="global", country="ZZ")
    assert filtered == []
    assert meta["matched_count"] == 0
    assert meta["silent_global_fallback"] is False


def test_build_wrapper_preserves_base_schema_and_adds_channel_contract(monkeypatch):
    from app import live_intelligence_channels_v350 as channels
    monkeypatch.setattr(channels.base, "build_live_intelligence", sample_base)
    payload = build_live_intelligence(Settings(external_live=False), channel="africa", limit=12)
    assert payload["schema"] == "sc-site-intelligence-live-intelligence/1.4"
    assert payload["channel"]["id"] == "africa"
    assert payload["count"] == 1
    assert payload["signals"][0]["signal_id"] == "human.ke"
    assert payload["display"]["topic_regional_channels_supported"] is True


def test_public_channel_routes(monkeypatch):
    monkeypatch.setattr(main, "build_live_intelligence", lambda *args, **kwargs: sample_base())
    monkeypatch.setattr(main, "build_channel_feed", lambda settings, channel_id, **kwargs: {**sample_base(), "channel": {"id": channel_id}})
    client = TestClient(main.app)
    assert client.get("/public/live-intelligence/channels").status_code == 200
    assert client.get("/public/live-intelligence/channel-policy").status_code == 200
    assert client.get("/public/live-intelligence/channels/weather-climate").status_code == 200
    feed = client.get("/public/live-intelligence/channels/africa/feed")
    assert feed.status_code == 200 and feed.json()["channel"]["id"] == "africa"
    assert client.get("/public/live-intelligence/channels/not-a-channel").status_code == 404


def test_unknown_channel_raises_key_error():
    with pytest.raises(KeyError):
        channel_definition("not-a-channel")
