from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app import unified_country_regional_dossiers as module
from app.main import app

client = TestClient(app)


def settings(**overrides):
    values = {
        "unified_dossiers_enabled": True,
        "unified_dossiers_max_records_per_domain": 12,
        "platform_core_enabled": True,
        "platform_core_url": "https://core.example.test",
        "platform_core_public_api_key": "test-public-key",
        "global_conditions_enabled": True,
        "economics_sustainability_enabled": True,
        "international_law_observatory_enabled": True,
        "scientific_earth_systems_enabled": True,
        "humanitarian_conflict_displacement_enabled": True,
        "trade_energy_resource_security_enabled": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


CATALOG = {
    "ok": True,
    "data_state": "cached",
    "countries": [
        {"code": "KEN", "iso2": "KE", "name": "Kenya", "region": "Sub-Saharan Africa", "latitude": -0.02, "longitude": 37.9},
        {"code": "GHA", "iso2": "GH", "name": "Ghana", "region": "Sub-Saharan Africa", "latitude": 7.95, "longitude": -1.02},
        {"code": "FRA", "iso2": "FR", "name": "France", "region": "Europe & Central Asia", "latitude": 46.2, "longitude": 2.2},
    ],
}


def baseline(code):
    return {
        "ok": True,
        "data_state": "cached",
        "country": next(c for c in CATALOG["countries"] if c["code"] == code),
        "highlights": [
            {"id": "SP.POP.TOTL", "label": "Population", "latest": {"value": 55_000_000, "year": 2024}, "unit": "people", "source": "World Bank", "source_id": "world-bank", "data_state": "cached"}
        ],
    }


def economic(*args, **kwargs):
    code = kwargs.get("geography_code") or "KEN"
    return {"integration": {"state": "connected"}, "records": [{"id": f"econ-{code}", "indicator_name": "GDP per capita", "source_id": "world-bank", "geography_code": code, "period": "2024", "value_number": 2000, "unit": "USD", "status": "official_release"}]}


def law(*args, **kwargs):
    code = kwargs.get("country") or "KEN"
    return {"integration": {"state": "connected"}, "records": [{"id": f"law-{code}", "title": "Official treaty record", "source_id": "un-treaty", "countries": [code], "published_at": "2025-01-01", "record_type": "treaty"}]}


def science(*args, **kwargs):
    return {"integration": {"state": "connected"}, "records": [{"id": "science-1", "title": "Earth observation collection", "source_id": "nasa-cmr", "published_at": "2025-02-01", "record_type": "earth_science_dataset"}]}


def humanitarian(*args, **kwargs):
    code = kwargs.get("country") or "KEN"
    return {"state": "connected", "records": [{"id": f"human-{code}", "title": "Humanitarian situation report", "source_id": "reliefweb", "countries": [code], "date": "2025-03-01", "category": "humanitarian"}]}


def humanitarian_records(*args, **kwargs):
    return {"state": "connected", "records": [
        {"id": "human-KEN", "title": "Kenya report", "source_id": "reliefweb", "countries": ["KEN"], "date": "2025-03-01", "category": "humanitarian"},
        {"id": "human-GHA", "title": "Ghana report", "source_id": "reliefweb", "countries": ["GHA"], "date": "2025-03-02", "category": "humanitarian"},
    ]}


def resources(*args, **kwargs):
    code = kwargs.get("country") or "KEN"
    return {"integration": {"state": "connected"}, "records": [{"id": f"resource-{code}", "indicator_name": "Renewable electricity", "source_id": "eia", "geography_code": code, "period": "2024", "value_number": 42, "unit": "percent", "family": "energy"}]}


def resource_records(*args, **kwargs):
    return {"integration": {"state": "connected"}, "records": [
        {"id": "resource-KEN", "indicator_name": "Imports", "source_id": "un-comtrade", "geography_code": "KEN", "period": "2024", "value_number": 10, "unit": "USD", "family": "trade"},
        {"id": "resource-GHA", "indicator_name": "Imports", "source_id": "un-comtrade", "geography_code": "GHA", "period": "2024", "value_number": 8, "unit": "USD", "family": "trade"},
    ]}


def conditions(*args, **kwargs):
    return {"state": "connected", "features": [{"id": "condition-1", "title": "Observed condition", "source_id": "met-no", "observed_at": "2025-04-01", "record_type": "observation"}]}


def install_fakes(monkeypatch):
    monkeypatch.setattr(module, "country_catalog", lambda: CATALOG)
    monkeypatch.setattr(module, "country_regions", lambda: {"regions": [{"name": "Sub-Saharan Africa", "country_count": 2}, {"name": "Europe & Central Asia", "country_count": 1}]})
    monkeypatch.setattr(module, "country_profile", baseline)
    import app.economics_markets_sustainability as economics
    import app.global_conditions_observatory as global_conditions
    import app.humanitarian_conflict_displacement_observatory as humanitarian_module
    import app.international_law_observatory as law_module
    import app.scientific_earth_systems_observatory as science_module
    import app.trade_energy_resource_security_observatory as resources_module
    monkeypatch.setattr(economics, "build_economic_records", economic)
    monkeypatch.setattr(global_conditions, "build_global_conditions_features", conditions)
    monkeypatch.setattr(law_module, "build_law_records", law)
    monkeypatch.setattr(science_module, "build_science_records", science)
    monkeypatch.setattr(humanitarian_module, "build_country_profile", humanitarian)
    monkeypatch.setattr(humanitarian_module, "build_records", humanitarian_records)
    monkeypatch.setattr(resources_module, "build_country_profile", resources)
    monkeypatch.setattr(resources_module, "build_records", resource_records)


def test_country_dossier_preserves_domains_without_score(monkeypatch):
    install_fakes(monkeypatch)
    payload = module.build_country_dossier(settings(), country="KEN", limit_per_domain=8)
    assert payload["country"]["name"] == "Kenya"
    assert set(payload["domains"]) == set(module.DOMAIN_LABELS)
    assert payload["counts"]["domains_with_records"] == 7
    assert "score" not in payload and "ranking" not in payload
    assert payload["domains"]["law"]["sample_records"][0]["record_type"] == "treaty"


def test_region_dossier_filters_member_countries_and_does_not_sum_values(monkeypatch):
    install_fakes(monkeypatch)
    payload = module.build_regional_dossier(settings(), region="Sub-Saharan Africa", limit_per_domain=8)
    assert payload["country_codes"] == ["GHA", "KEN"]
    assert payload["domains"]["resources"]["record_count"] == 2
    assert "score" not in payload and "ranking" not in payload
    assert payload["counts"]["countries"] == 2


def test_comparison_aligns_coverage_without_difference(monkeypatch):
    install_fakes(monkeypatch)
    payload = module.build_dossier_comparison(settings(), country_a="KEN", country_b="GHA", limit_per_domain=5)
    assert payload["methodology"]["composite_score_created"] is False
    assert payload["methodology"]["differences_calculated"] is False
    assert len(payload["coverage_matrix"]) == 7


def test_disabled_and_invalid_subject_states(monkeypatch):
    install_fakes(monkeypatch)
    disabled = module.build_country_dossier(settings(unified_dossiers_enabled=False), country="KEN")
    assert disabled["state"] == "disabled" and disabled["domains"] == {}
    try:
        module.build_country_dossier(settings(), country="ZZZ")
    except ValueError as exc:
        assert str(exc) == "unsupported_country"
    else:
        raise AssertionError("unsupported country should fail")


def test_public_routes(monkeypatch):
    install_fakes(monkeypatch)
    from app.config import get_settings
    get_settings.cache_clear()
    urls = [
        "/public/intelligence-dossiers",
        "/public/intelligence-dossiers/facets",
        "/public/intelligence-dossiers/country?country=KEN&limit_per_domain=5",
        "/public/intelligence-dossiers/region?region=Sub-Saharan%20Africa&limit_per_domain=5",
        "/public/intelligence-dossiers/compare?country_a=KEN&country_b=GHA&limit_per_domain=5",
        "/public/intelligence-dossiers/brief?country=KEN&limit_per_domain=5",
        "/public/intelligence-dossiers/diagnostics",
    ]
    assert all(client.get(url).status_code == 200 for url in urls)


def test_interface_wordpress_and_release_contract():
    root = Path(__file__).resolve().parents[2]
    html = (root / "backend/public_app/index.html").read_text()
    js = (root / "backend/public_app/assets/dossiers-v270.js").read_text()
    css = (root / "backend/public_app/assets/dossiers-v270.css").read_text()
    app_js = (root / "backend/public_app/assets/app.js").read_text()
    php = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert 'data-route="dossiers"' in html and 'id="dossierStudio"' in html
    assert "SCDossiersV270" in js and ".dossier-studio" in css
    assert 'const APP_VERSION="2.13.0"' in app_js
    assert "Version: 2.13.0" in php and "sc_country_regional_intelligence_dossiers" in php
    assert "No composite score or country ranking" in html
