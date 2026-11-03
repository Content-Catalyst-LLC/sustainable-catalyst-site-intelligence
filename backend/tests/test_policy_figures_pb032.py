import hashlib,json,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from scientific_policy_figures_pb032 import render_policy_figures, _check_register
FIX=Path(__file__).resolve().parents[2]/"fixtures"/"wexford_field_evidence.json"


def test_two_required_figures(tmp_path):
    m=render_policy_figures(FIX,tmp_path)
    assert set(m["figures"])=={"FIG-PB01","FIG-PB02"}
    for fig in m["figures"].values():
        for k in ("png","svg"):
            p=tmp_path/fig[k]["filename"]
            assert p.stat().st_size>2000
            assert hashlib.sha256(p.read_bytes()).hexdigest()==fig[k]["sha256"]
    assert m["publication"]["eligible"] is False


def test_evidence_input_lacks_doi_rejected():
    m=json.loads(FIX.read_text());del m["studies"][0]["doi"]
    with pytest.raises(ValueError,match="doi"):_check_register(m)


def test_incomplete_evidence_warning_rejected():
    m=json.loads(FIX.read_text());m["cross_study_warning"]=""
    with pytest.raises(ValueError,match="warning"):_check_register(m)


def test_non_wexford_domain_reuse(tmp_path):
    m=json.loads(FIX.read_text());m["studies"][0]["location"]="Research site A";m["studies"][1]["location"]="Research site B"
    p=tmp_path/"other_project_evidence.json";p.write_text(json.dumps(m))
    result=render_policy_figures(p,tmp_path/"out")
    assert result["figures"]["FIG-PB01"]["png"]["bytes"]>0


def test_duplicate_study_ids_rejected():
    m=json.loads(FIX.read_text());m["studies"][1]["id"]=m["studies"][0]["id"]
    with pytest.raises(ValueError,match="Duplicate"):_check_register(m)