"""v4.59.0 multi-variable contracts: no false live-data claims."""
from pathlib import Path
import pytest
from backend.app.ocean_contracts_v4590 import registry,normalize_record

ROOT=Path(__file__).resolve().parents[1]
HASH="a"*64

def test_registry_distinguishes_defined_from_live():
    info=registry()
    assert info["schema"]=="scsi-ocean-variable-registry/4.59.0"
    assert len(info["variables"])==7
    status={x["id"]:x["retrieval_status"] for x in info["variables"]}
    assert status["sea-surface-temperature"]=="live-verified"
    assert all(v=="not-connected" for k,v in status.items() if k!="sea-surface-temperature")
    assert len(info["sources"])==2
    sources={s["id"]:s for s in info["sources"]}
    assert sources["noaa-mur-sst"]["capability"]=="live-verified"
    assert sources["noaa-snpp-chlorophyll-monthly"]["capability"]=="integration-pending"
    assert status["chlorophyll-a"]=="not-connected"
    assert info["policy"]["forecasts_are_not_observations"]

def test_normalized_sst_and_receipt():
    data=normalize_record(variable_id="sea-surface-temperature",source_id="noaa-mur-sst",
      value=26.6,unit="degC",latitude=0,longitude=0,observed_at="2026-10-01T09:00:00Z",
      evidence_type="satellite-derived",receipt={"response_sha256":HASH})
    assert data["measurement"]["value"]==26.6
    assert data["provenance"]["scientific_accuracy_independently_verified"] is False

@pytest.mark.parametrize("change",[
    {"unit":"K"},{"value":float("nan")},{"source_id":"not-a-source"},
    {"evidence_type":"forecast"},{"observed_at":"2026-10-01"},
    {"latitude":91},{"receipt":{}},{"variable_id":"surface-current"}
])
def test_fail_closed(change):
    values=dict(variable_id="sea-surface-temperature",source_id="noaa-mur-sst",
       value=26.6,unit="degC",latitude=0,longitude=0,observed_at="2026-10-01T09:00:00Z",
       evidence_type="satellite-derived",receipt={"response_sha256":HASH})
    values.update(change)
    with pytest.raises(ValueError):normalize_record(**values)

def test_frontend_registry_is_explicit_and_additive():
    script=(ROOT/"web/app/assets/ocean-variable-registry-v4590.js").read_text()
    assert "not connected" in script
    assert "scsi:ocean-surface-enter" in script
    assert "variables/registry" in script
    for name in ("web/index.html","web/app/index.html"):
        assert 'ocean-variable-registry-v4590.js?v=4.59.0' in (ROOT/name).read_text()
