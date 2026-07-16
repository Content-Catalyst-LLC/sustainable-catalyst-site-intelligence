from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app import comparative_scenario_studio_v290 as module

client = TestClient(app)


def settings(**overrides):
    base = {
        "comparative_scenario_studio_enabled": True,
        "comparative_scenario_max_geographies": 5,
        "comparative_scenario_max_indicators": 12,
        "comparative_scenario_max_records": 400,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def records():
    return [
        {"id":"a1","domain":"economics","indicator_code":"GDP","indicator_name":"GDP","geography_code":"KEN","period":"2024","value_number":100.0,"unit":"USD","frequency":"ANNUAL","price_basis":"current","seasonal_adjustment":"","source_id":"world-bank","source_url":"https://example.org/a"},
        {"id":"a2","domain":"economics","indicator_code":"GDP","indicator_name":"GDP","geography_code":"GHA","period":"2024","value_number":80.0,"unit":"USD","frequency":"ANNUAL","price_basis":"current","seasonal_adjustment":"","source_id":"world-bank","source_url":"https://example.org/b"},
        {"id":"b1","domain":"economics","indicator_code":"CPI","indicator_name":"Inflation","geography_code":"KEN","period":"2024","value_number":5.0,"unit":"percent","frequency":"ANNUAL","price_basis":"","seasonal_adjustment":"","source_id":"world-bank","source_url":"https://example.org/c"},
        {"id":"b2","domain":"economics","indicator_code":"CPI","indicator_name":"Inflation","geography_code":"GHA","period":"2024-Q4","value_number":6.0,"unit":"index","frequency":"QUARTERLY","price_basis":"","seasonal_adjustment":"seasonally adjusted","source_id":"imf","source_url":"https://example.org/d?api_key=secret"},
    ]


def fake_collect(settings, **kwargs):
    selected = set(kwargs.get("geographies") or [])
    indicators = {x.lower() for x in kwargs.get("indicators") or []}
    result = [r for r in records() if r["geography_code"] in selected]
    if indicators:
        result = [r for r in result if r["indicator_code"].lower() in indicators]
    return result, [{"state":"connected"}]


def test_comparison_matrix_preserves_compatibility(monkeypatch):
    monkeypatch.setattr(module, "_collect_records", fake_collect)
    payload = module.build_comparison_matrix(settings(), geographies=["KEN","GHA"], indicators=["GDP","CPI"])
    assert payload["geographies"] == ["KEN","GHA"]
    by_code = {row["indicator_code"]: row for row in payload["rows"]}
    assert by_code["GDP"]["compatibility"]["compatible_for_direct_difference"] is True
    assert by_code["CPI"]["compatibility"]["compatible_for_direct_difference"] is False
    assert payload["methodology"]["silent_normalization"] is False


def test_scenario_is_hypothetical_not_forecast(monkeypatch):
    monkeypatch.setattr(module, "_collect_records", fake_collect)
    payload = module.build_transparent_scenario(settings(), geographies=["KEN","GHA"], indicators=["GDP"], adjustments=[{"indicator_code":"GDP","geography_code":"KEN","mode":"percent","value":10}])
    result = payload["results"][0]
    assert result["baseline"] == 100.0 and abs(result["scenario"] - 110.0) < 1e-9
    assert payload["methodology"]["hypothetical"] is True
    assert payload["methodology"]["forecast"] is False
    assert payload["methodology"]["causal_model"] is False


def test_incompatible_scenario_is_withheld(monkeypatch):
    monkeypatch.setattr(module, "_collect_records", fake_collect)
    payload = module.build_transparent_scenario(settings(), geographies=["KEN","GHA"], indicators=["CPI"], adjustments=[{"indicator_code":"CPI","mode":"absolute","value":1}])
    assert payload["results"] == []
    assert len(payload["skipped"]) == 2


def test_correlation_requires_overlap_and_disclaims_causation(monkeypatch):
    from app import economics_markets_sustainability as economics
    def fake_series(settings, *, indicator_code, geography_code, limit):
        values = [1,2,3,4] if indicator_code == "X" else [2,4,6,8]
        return {"points":[{"period":str(2020+i),"value_number":value} for i,value in enumerate(values)]}
    monkeypatch.setattr(economics, "build_economic_series", fake_series)
    payload = module.build_correlation_review(settings(), geography="KEN", indicator_x="X", indicator_y="Y")
    assert payload["pearson_correlation"] == 1.0
    assert payload["sufficient_overlap"] is True
    assert payload["methodology"]["causal_inference"] is False


def test_packet_has_integrity_and_no_ranking(monkeypatch):
    monkeypatch.setattr(module, "_collect_records", fake_collect)
    payload = module.build_comparison_packet(settings(), payload={"geographies":["KEN","GHA"],"indicators":["GDP"],"title":"Test packet"})
    assert len(payload["integrity"]["digest"]) == 64
    assert "No ranking" in payload["responsible_use"][0]
    assert payload["comparison"]["methodology"]["ranking_created"] is False


def test_public_routes_and_interface(monkeypatch):
    monkeypatch.setattr(module, "_collect_records", fake_collect)
    assert client.get("/public/comparative-scenario-studio").status_code == 200
    compare = client.post("/public/comparative-scenario-studio/compare", json={"geographies":["KEN","GHA"],"indicators":["GDP"]})
    assert compare.status_code == 200 and compare.json()["rows"]
    scenario = client.post("/public/comparative-scenario-studio/scenario", json={"geographies":["KEN","GHA"],"indicators":["GDP"],"adjustments":[{"indicator_code":"GDP","mode":"percent","value":5}]})
    assert scenario.status_code == 200
    packet = client.post("/public/comparative-scenario-studio/packet", json={"geographies":["KEN","GHA"],"indicators":["GDP"]})
    assert packet.status_code == 200 and packet.json()["integrity"]["algorithm"] == "sha256"
    root = Path(__file__).resolve().parents[2]
    html = (root / "backend/public_app/index.html").read_text()
    js = (root / "backend/public_app/assets/scenarios-v290.js").read_text()
    css = (root / "backend/public_app/assets/scenarios-v290.css").read_text()
    app_js = (root / "backend/public_app/assets/app.js").read_text()
    php = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert 'data-route="scenarios"' in html and 'id="scenarioStudio"' in html
    assert "SCScenariosV290" in js and ".scenario-studio" in css
    assert 'const APP_VERSION="2.18.0"' in app_js
    assert "Version: 2.18.0" in php and "sc_comparative_intelligence_scenario_studio" in php
