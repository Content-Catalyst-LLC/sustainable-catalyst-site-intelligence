from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app import live_country_intelligence as live
from app.workspace_evidence_unification_v4358 import (
    canonicalize_country_indicator,
    canonical_country_indicator,
    canonical_country_observations,
    overview,
    readiness,
)
from app.record_provenance_v4358 import public_indicator_record_truth, public_country_record_truth, public_record_truth_manifest


def _country():
    return {"code":"PSE","iso2":"PS","name":"Palestine","display_name":"Palestine"}


def _indicator(value=100.0, year=2024, state="live"):
    latest = None if value is None else {"year":year,"value":value,"unit":"% of population"}
    return {
        "id":"EG.ELC.ACCS.ZS","key":"electricity_access","label":"Access to electricity","domain":"Infrastructure",
        "unit":"% of population","format":"percent","latest":latest,"series":[],"source_id":"EG.ELC.ACCS.ZS",
        "source":"World Bank Open Data","source_url":"https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS?locations=PS",
        "data_state":state if latest else "unavailable","cache_state":state if latest else "unavailable",
        "retrieved_at":"2026-08-11T05:00:00+00:00" if latest else None,"stale":False,"lineage":{"platform_core_state":"not-recorded"},
    }


def _payload(value=100.0, year=2024, state="live"):
    return {"ok":True,"version":"4.35.15","country":_country(),"data_state":state,"indicators":[_indicator(value,year,state)]}


def test_canonical_observation_preserves_value_semantics_and_fingerprint():
    obs=canonicalize_country_indicator(_country(),_indicator())
    assert obs["observation_id"]=="country-indicator:PSE:EG.ELC.ACCS.ZS"
    assert obs["value"]=={"number":100.0,"text":"100.0","available":True}
    assert obs["semantics"]["concept_id"]=="electricity_structural_access"
    assert "current electricity availability" in obs["semantics"]["forbidden_substitutions"]
    assert len(obs["fingerprint"]["value"])==64


def test_canonical_missing_value_stays_missing():
    obs=canonicalize_country_indicator(_country(),_indicator(None))
    assert obs["value"]["number"] is None
    assert obs["value"]["available"] is False
    assert obs["truth_state"]=="missing"


def test_country_indicator_resolves_the_same_live_record(monkeypatch):
    monkeypatch.setattr(live,"country_indicators",lambda _code:_payload())
    obs=canonical_country_indicator("PSE","EG.ELC.ACCS.ZS")
    assert obs["value"]["number"]==100.0
    assert obs["presentation_state"]=="live"


def test_country_catalog_and_indicator_share_canonical_fingerprint(monkeypatch):
    monkeypatch.setattr(live,"country_indicators",lambda _code:_payload())
    one=canonical_country_indicator("PSE","EG.ELC.ACCS.ZS")
    catalog=canonical_country_observations("PSE")
    assert catalog["observations"][0]["fingerprint"]["value"]==one["fingerprint"]["value"]


def test_truth_consumes_canonical_live_observation_not_packaged_snapshot(monkeypatch):
    monkeypatch.setattr(live,"country_indicators",lambda _code:_payload(100.0,2024,"live"))
    truth=public_indicator_record_truth(Settings(_env_file=None),"PSE","EG.ELC.ACCS.ZS")
    assert truth["value"]["number"]==100.0
    assert truth["value"]["available"] is True
    assert truth["canonical_observation"]["value"]["number"]==100.0
    assert truth["canonical_observation_sha256"]==truth["canonical_observation"]["fingerprint"]["value"]
    assert truth["presentation_state"]=="live"


def test_truth_and_workspace_both_missing_when_canonical_value_missing(monkeypatch):
    monkeypatch.setattr(live,"country_indicators",lambda _code:_payload(None,None,"unavailable"))
    obs=canonical_country_indicator("PSE","EG.ELC.ACCS.ZS")
    truth=public_indicator_record_truth(Settings(_env_file=None),"PSE","EG.ELC.ACCS.ZS")
    assert obs["value"]["available"] is False
    assert truth["value"]["available"] is False
    assert truth["truth_state"]=="missing"


def test_country_truth_catalog_uses_same_observations(monkeypatch):
    monkeypatch.setattr(live,"country_indicators",lambda _code:_payload())
    catalog=public_country_record_truth(Settings(_env_file=None),"PSE")
    assert catalog["record_count"]==1
    assert catalog["records"][0]["canonical_observation"]["observation_id"]=="country-indicator:PSE:EG.ELC.ACCS.ZS"


def test_truth_manifest_pairs_canonical_and_truth_fingerprints(monkeypatch):
    monkeypatch.setattr(live,"country_indicators",lambda _code:_payload())
    manifest=public_record_truth_manifest(Settings(_env_file=None),"PSE")
    entry=manifest["entries"][0]
    assert len(entry["canonical_observation_sha256"])==64
    assert len(entry["record_truth_sha256"])==64


def test_country_indicators_attach_canonical_observation(monkeypatch):
    monkeypatch.setattr(live,"_country",lambda _code:("PSE",{"iso2":"PS","name":"Palestine"}))
    monkeypatch.setattr(live,"_live_indicator_bundle",lambda _code:tuple(_indicator(100.0,2024,"live") if d["id"]=="EG.ELC.ACCS.ZS" else {**d,"latest":None,"series":[],"source_id":d["id"],"source":"World Bank Open Data","source_url":"x","data_state":"unavailable","cache_state":"unavailable","retrieved_at":None,"stale":False} for d in live.INDICATORS))
    payload=live.country_indicators("PSE")
    electricity=next(row for row in payload["indicators"] if row["id"]=="EG.ELC.ACCS.ZS")
    assert electricity["canonical_observation"]["value"]["number"]==100.0
    assert electricity["canonical_observation"]["semantics"]["concept_id"]=="electricity_structural_access"


def test_workspace_profile_reads_canonical_observation(monkeypatch):
    row=_indicator(100.0,2024,"live")
    row["canonical_observation"]=canonicalize_country_indicator(_country(),row)
    monkeypatch.setattr(live,"country_indicators",lambda _code:{"ok":True,"generated_at":"x","country":_country(),"data_state":"live","stale":False,"indicators":[row],"missing_indicators":[],"state_counts":{}})
    profile=live.country_profile("PSE")
    item=profile["highlights"][0]
    assert item["value"]==item["canonical_observation"]["value"]["number"]
    assert item["canonical_observation_sha256"]==item["canonical_observation"]["fingerprint"]["value"]
    assert item["truth_endpoint"].endswith("/PSE/EG.ELC.ACCS.ZS")


def test_overview_and_readiness_are_network_free():
    assert overview()["network_calls_performed"] is False
    result=readiness()
    assert result["ok"] is True and result["network_calls_performed"] is False


def test_public_routes_and_frontend_truth_control_exist():
    client=TestClient(app)
    assert client.get("/public/workspace-evidence").status_code==200
    assert client.get("/public/workspace-evidence/readiness").status_code==200
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    js=(root/"backend/public_app/assets/app.js").read_text()
    truth_js=(root/"backend/public_app/assets/record-provenance-v3238.js").read_text()
    assert 'data-record-truth-indicator' in js
    assert 'data-canonical-observation' in js
    assert 'Canonical observation' in truth_js and 'Canonical SHA-256' in truth_js
