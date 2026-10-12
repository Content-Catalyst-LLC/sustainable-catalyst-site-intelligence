"""v4.57.7 bounded NOAA SST grid: mocked source CSV tests."""
from pathlib import Path
import pytest
from backend.app.noaa_grid_v4577 import retrieve_grid

SAMPLE=b"time,latitude,longitude,analysed_sst\nUTC,degrees_north,degrees_east,degree_C\n2026-10-01T09:00:00Z,12.0,-65.0,28.561\n2026-10-01T09:00:00Z,12.1,-65.0,NaN\n"

def test_grid_data_and_receipt():
    result=retrieve_grid(12,-65,"2026-10-01",transport=lambda url:SAMPLE)
    assert result["status"]=="retrieved"
    assert len(result["cells"])==1
    assert result["missing_count"]==1
    assert result["cells"][0]["value"]==28.561
    assert result["receipt"]["response_sha256"]
    assert ":10:" in result["receipt"]["source_url"]

def test_absent_grid_is_not_zero():
    result=retrieve_grid(12,-65,"2026-10-01",transport=lambda url:SAMPLE.replace(b"28.561",b"NaN"))
    assert result["status"]=="no_data" and result["cells"]==[]

def test_upstream_error():
    def broken(url):raise ValueError("unavailable")
    assert retrieve_grid(12,-65,"2026-10-01",transport=broken)["status"]=="unavailable"

@pytest.mark.parametrize("lat,lon,day",[(90,0,"2026-10-01"),(0,179,"2026-10-01"),(0,0,"invalid")])
def test_bad_boundaries(lat,lon,day):
    with pytest.raises(ValueError):retrieve_grid(lat,lon,day,transport=lambda url:SAMPLE)

def test_renderer_and_frontend_registration():
    root=Path(__file__).resolve().parents[1]
    script=(root/"web/app/assets/ocean-surface-visualization-v4575.js").read_text()
    assert "/public/ocean-intelligence/noaa/sst/grid" in script
    assert "ocean4577Grid" in script
    assert "ocean4577Fetch" in script
    for name in ("web/index.html","web/app/index.html"):
        assert "v4575.js?v=4.58.0" in (root/name).read_text()


def test_interactive_cell_inspector_and_truthful_fallback():
    root=Path(__file__).resolve().parents[1]
    script=(root/'web/app/assets/ocean-surface-visualization-v4575.js').read_text()
    for part in ('data-ocean-cell', 'ocean4578Detail', 'ocean4578ZoomIn', 'ocean4578ZoomOut', 'ocean4578ZoomReset','ocean4578Locator','activeGrid.receipt.response_sha256'):
        assert part in script
    assert 'no interpolation, land mask, or basemap inferred' in script


def test_v4579_comparison_export_provenance_contracts():
    root=Path(__file__).resolve().parents[1]
    js=(root/"web/app/assets/ocean-surface-visualization-v4575.js").read_text()
    for term in ("ocean4579Date","ocean4579Fetch","ocean4579Export","ocean4579Difference","scsi-noaa-sst-comparison/1.0","scsi-ocean-evidence-package/4.57.9","response_sha256","unmatched_first","unmatched_second","scientific_accuracy_independently_verified:false","Exact 4-decimal latitude/longitude keys"):
        assert term in js
    assert "v4575.js?v=4.58.0" in (root/"web/index.html").read_text()
