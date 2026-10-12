"""NOAA SST connector tests: network mocked; no external dependency."""
from pathlib import Path
import pytest
from backend.app.noaa_erddap_v4576 import retrieve_sst

SAMPLE = b"time,latitude,longitude,analysed_sst\nUTC,degrees_north,degrees_east,degree_C\n2026-10-01T00:00:00Z,12.0,-65.0,28.4\n"

def test_verified_single_point_receipt():
    got=retrieve_sst(12,-65,"2026-10-01",transport=lambda url: SAMPLE)
    assert got["status"]=="retrieved"
    assert got["observation"]["value"]==28.4
    assert got["receipt"]["response_sha256"]
    assert "jplMURSST41" in got["receipt"]["source_url"]

def test_no_data_is_not_zero():
    got=retrieve_sst(12,-65,"2026-10-01",transport=lambda url:SAMPLE.replace(b"28.4",b"NaN"))
    assert got["status"]=="no_data" and got["observation"] is None

def test_upstream_failure_not_fabricated():
    def broken(url): raise ValueError("ERDDAP unavailable")
    got=retrieve_sst(12,-65,"2026-10-01",transport=broken)
    assert not got["ok"] and got["observation"] is None

@pytest.mark.parametrize("lat,lon,day",[(99,0,"2026-10-01"),(0,0,"wrong"),(float("nan"),0,"2026-10-01")])
def test_bad_inputs_rejected(lat,lon,day):
    with pytest.raises(ValueError):retrieve_sst(lat,lon,day,transport=lambda url:SAMPLE)

def test_frontend_wired():
    root=Path(__file__).resolve().parents[1]
    js=(root/"web/app/assets/ocean-surface-visualization-v4575.js").read_text()
    assert "/public/ocean-intelligence/noaa/sst" in js
    assert "ocean4576Fetch" in js
    for p in ("web/index.html","web/app/index.html"):
        assert "ocean-surface-visualization-v4575.js?v=4.57.6.1" in (root/p).read_text()


def test_original_ocean_evidence_panel_receives_retrieval():
    root=Path(__file__).resolve().parents[1]
    source=(root/'web/app/assets/ocean-surface-v4500.js').read_text()
    visualization=(root/'web/app/assets/ocean-surface-visualization-v4575.js').read_text()
    assert 'scsi:ocean-sst-retrieved' in source
    assert 'scsi:ocean-sst-retrieved' in visualization
    assert 'oceanTruth' in source
