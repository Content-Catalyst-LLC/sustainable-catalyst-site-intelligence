from pathlib import Path
from types import SimpleNamespace
from fastapi.testclient import TestClient
import pytest
from app.main import app
from app import research_paths_investigations_v2100 as module
client=TestClient(app)
def settings(**kw):
    base={"research_workflows_enabled":True,"research_workflows_max_investigations":30,"research_workflows_max_evidence_items":120,"research_workflows_max_notes":80};base.update(kw);return SimpleNamespace(**base)
def payload():
    return {"id":"inv-1","title":"Kenya food security review","research_question":"What does the evidence establish?","status":"active","countries":["KEN"],"domains":["economics","humanitarian"],"notes":[{"title":"Scope","body":"Use official sources."}],"evidence":[{"title":"Inflation","evidence_class":"official-statistic","domain":"economics","source_id":"world-bank","source_url":"https://example.org/value","value_number":5.2,"unit":"percent"}],"checkpoints":[{"label":"Initial review"}],"saved_views":[{"title":"Kenya dossier","route":"dossiers","url":"https://example.org/app/?view=dossiers"}]}
def test_investigation_normalization_and_integrity():
    out=module.normalize_investigation(payload(),settings());assert out["schema"].endswith("/1.0");assert out["privacy"]["server_persistence"] is False;assert len(out["integrity"]["digest"])==64;assert out["evidence"][0]["evidence_class"]=="official-statistic"
def test_sensitive_fields_rejected():
    bad=payload();bad["api_key"]="secret"
    with pytest.raises(ValueError):module.normalize_investigation(bad,settings())
def test_evidence_and_briefing_preserve_classes():
    evidence=module.build_evidence_set(payload(),settings());brief=module.build_briefing_packet(payload(),settings());assert evidence["evidence_count"]==1;assert brief["editorial_controls"]["automatic_claim_generation"] is False;assert brief["sections"][0]["evidence"][0]["evidence_class"]=="official-statistic"
def test_handoffs_are_structured_and_reviewable():
    out=module.build_product_handoff(payload(),"decision-studio",settings());assert out["target"]=="decision-studio";assert out["constraints"]["human_review_required"] is True;assert out["constraints"]["automatic_publication"] is False

def test_public_routes_and_interface():
    assert client.get("/public/research-workflows").status_code==200
    assert client.get("/public/research-workflows/schema").status_code==200
    assert client.post("/public/research-workflows/validate",json=payload()).status_code==200
    assert client.post("/public/research-workflows/evidence-set",json=payload()).status_code==200
    assert client.post("/public/research-workflows/briefing",json=payload()).status_code==200
    assert client.post("/public/research-workflows/handoff/workbench",json=payload()).status_code==200
    root=Path(__file__).resolve().parents[2];html=(root/"backend/public_app/index.html").read_text();js=(root/"backend/public_app/assets/research-v2100.js").read_text();css=(root/"backend/public_app/assets/research-v2100.css").read_text();appjs=(root/"backend/public_app/assets/app.js").read_text();php=(root/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert 'data-route="research"' in html and 'id="researchWorkflowStudio"' in html
    assert "SCResearchV2100" in js and ".research-workflow-studio" in css
    assert 'const APP_VERSION="3.19.0"' in appjs
    assert "Version: 3.19.0" in php and "sc_research_paths_investigations" in php
