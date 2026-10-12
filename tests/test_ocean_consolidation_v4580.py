"""v4.58.0 production consolidation tests."""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("certifier",ROOT/"scripts/certify-ocean-evidence-v4580.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def package():
    def grid(day,values,hash_character):
        return {"date":day,"status":"retrieved","unit":"degC","cells":[{"latitude":0,"longitude":0,"value":values[0]},{"latitude":0,"longitude":0.1,"value":values[1]}],"receipt":{"dataset_id":"jplMURSST41","variable_id":"analysed_sst","source_url":"https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41.csv?a","response_sha256":hash_character*64}}
    a=grid("2026-10-01",[25,26],"a");b=grid("2026-10-02",[25.2,26.4],"b")
    return {"primary_grid":a,"comparison_grid":b,"comparison":{"matching_cells":2,"unmatched_first":0,"unmatched_second":0,"cells":[{"latitude":0,"longitude":0,"first":25,"second":25.2,"delta":0.2},{"latitude":0,"longitude":0.1,"first":26,"second":26.4,"delta":0.4}],"mean_delta":0.3},"receipt_assessment":{"scientific_accuracy_independently_verified":False}}

def test_consistent_package():
    assert mod.certify(package())==[]

def test_detects_falsified_change():
    p=package();p["comparison"]["cells"][0]["delta"]=4.5
    assert any("Difference mismatch" in x for x in mod.certify(p))

def test_detects_mean_error_and_missing_receipt():
    p=package();p["comparison"]["mean_delta"]=2
    p["primary_grid"]["receipt"]["response_sha256"]="bad"
    issues=mod.certify(p)
    assert any("Mean difference mismatch" in x for x in issues)
    assert any("receipt hash invalid" in x for x in issues)

def test_ocean_assets_and_release():
    js=(ROOT/"web/app/assets/ocean-surface-visualization-v4575.js").read_text()
    assert "ocean4579Export" in js
    assert "scsi:ocean-sst-retrieved" in js
    for path in ("web/index.html","web/app/index.html"):
        assert "v4575.js?v=4.58.0" in (ROOT/path).read_text()
