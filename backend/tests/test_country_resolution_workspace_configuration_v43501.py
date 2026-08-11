from types import SimpleNamespace

import pytest

from app import live_country_intelligence as countries
from app import unified_public_intelligence_v4000 as unified


def test_pse_canonical_display_name_and_aliases():
    row = countries._normalize_country(
        "PSE",
        {
            "name": "West Bank and Gaza",
            "iso2": "PS",
            "region": "Middle East, North Africa, Afghanistan & Pakistan",
        },
    )
    assert row["name"] == "Palestine"
    assert row["display_name"] == "Palestine"
    assert row["source_name"] == "West Bank and Gaza"
    assert {"State of Palestine", "Palestinian Territories", "Palestinian Territory", "West Bank and Gaza"} <= set(row["alternate_names"])


def test_pse_remains_in_offline_catalog():
    row = countries._normalized_static_catalog()["PSE"]
    assert row["name"] == "Palestine"
    assert row["iso2"] == "PS"


@pytest.mark.parametrize(
    "query",
    ["PSE", "PS", "Palestine", "State of Palestine", "Palestinian Territories", "Palestinian Territory", "West Bank and Gaza"],
)
def test_country_resolver_routes_all_palestine_aliases_to_pse(monkeypatch, query):
    row = countries._normalized_static_catalog()["PSE"]
    monkeypatch.setattr(countries, "country_catalog", lambda *args, **kwargs: {"countries": [{"code": "PSE", **row}]})
    code, metadata = countries._country(query)
    assert code == "PSE"
    assert metadata["name"] == "Palestine"
    assert metadata["iso2"] == "PS"


def _settings(**overrides):
    values = {
        "platform_core_enabled": False,
        "platform_core_url": "",
        "platform_core_public_api_key": "",
        "platform_core_write_api_key": "",
    }
    for attribute in unified.WORKSPACE_FLAG_MAP.values():
        values[attribute] = True
    values.update(overrides)
    return SimpleNamespace(**values)


def test_v4_readiness_distinguishes_structural_from_runtime_configuration():
    payload = unified.public_v4_readiness(_settings())
    assert payload["ok"] is True
    assert payload["runtime_ready"] is False
    assert payload["configuration_required"] is True
    assert payload["runtime_configuration"]["core_required_routes_unavailable"] == ["economics", "law", "science", "resources"]
    assert payload["runtime_configuration"]["platform_core"]["public_read_configured"] is False


def test_v4_configuration_ready_with_core_read_bridge():
    payload = unified.public_v4_configuration_readiness(
        _settings(platform_core_enabled=True, platform_core_url="https://core.example.test")
    )
    assert payload["ok"] is True
    assert payload["runtime_ready"] is True
    assert payload["configuration_required"] is False
    assert payload["core_required_routes_unavailable"] == []
    assert payload["platform_core"]["public_read_configured"] is True
    assert payload["platform_core"]["public_api_key_optional"] is True
