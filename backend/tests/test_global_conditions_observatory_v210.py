from types import SimpleNamespace

from app import global_conditions_observatory as module


def settings(**overrides):
    values = {
        "platform_core_enabled": True,
        "platform_core_url": "https://core.example.test",
        "platform_core_public_api_key": "test-public-key",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_disabled_core_returns_public_local_fallback(monkeypatch):
    monkeypatch.setenv("SC_SI_GLOBAL_CONDITIONS_ENABLED", "true")
    result = module.build_global_conditions_overview(
        settings(platform_core_enabled=False, platform_core_url="")
    )
    assert result["ok"] is True
    assert result["integration"]["state"] == "local-fallback"
    assert result["integration"]["credential_exposed"] is False
    assert result["capabilities"]["paid_provider_required"] is False


def test_bbox_validation_rejects_invalid_order():
    try:
        module._validate_bbox("10,20,-10,30")
    except ValueError as exc:
        assert "minimums" in str(exc)
    else:
        raise AssertionError("invalid bbox was accepted")


def test_feature_proxy_sanitizes_private_properties(monkeypatch):
    monkeypatch.setattr(
        module,
        "_core_json",
        lambda *args, **kwargs: {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "feature-1",
                    "geometry": {"type": "Point", "coordinates": [20, 10]},
                    "properties": {
                        "title": "Visible feature",
                        "domain": "weather",
                        "source_id": "met-no",
                        "api_key": "must-not-leak",
                        "private_url": "https://private.example.test",
                    },
                }
            ],
        },
    )
    result = module.build_global_conditions_features(settings(), limit=10)
    assert result["count"] == 1
    properties = result["features"][0]["properties"]
    assert properties["title"] == "Visible feature"
    assert "api_key" not in properties
    assert "private_url" not in properties


def test_layer_proxy_normalizes_unknown_layer_type(monkeypatch):
    monkeypatch.setattr(
        module,
        "_core_json",
        lambda *args, **kwargs: {"layers": [{"id": "x", "title": "X", "type": "secret"}]},
    )
    result = module.build_global_conditions_layers(settings())
    assert result["layers"][0]["layer_type"] == "geojson"


def test_diagnostics_never_return_api_key(monkeypatch):
    monkeypatch.setenv("SC_SI_GLOBAL_CONDITIONS_ENABLED", "true")
    result = module.build_global_conditions_diagnostics(settings())
    serialized = str(result)
    assert "test-public-key" not in serialized
    assert result["integration"]["credential_exposed"] is False
