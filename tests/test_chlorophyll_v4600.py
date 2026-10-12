"""4.60.0 NOAA chlorophyll source contract regression tests."""
from pathlib import Path
from backend.app.chlorophyll_v4600 import retrieve_chlorophyll_grid
from backend.app.ocean_contracts_v4590 import registry
ROOT=Path(__file__).resolve().parents[1]
def mock(time="2026-09-15T12:00:00Z"):
 return ("time,latitude,longitude,chlor_a\nUTC,degrees_north,degrees_east,mg m-3\n"+time+",12,-65,0.14\n"+time+",12.1,-64.9,NaN\n").encode()

def test_valid_grid_receipt_and_missing_values():
 response=retrieve_chlorophyll_grid(12,-65,"2026-09-01",transport=lambda url:mock())
 assert response["ok"] and response["unit"]=="mg/m3"
 assert len(response["cells"])==1 and response["missing_count"]==1
 assert response["receipt"]["dataset_id"]=="noaa_snpp_chla_monthly"
 assert len(response["receipt"]["response_sha256"])==64
 assert response["composite_time"].startswith("2026-09")

def test_wrong_month_fails_closed():
 assert retrieve_chlorophyll_grid(12,-65,"2026-09-01",transport=lambda u:mock("2026-08-15T12:00:00Z"))["status"]=="unavailable"

def test_invalid_location_no_network():
 assert retrieve_chlorophyll_grid(80,-65,"2026-09-01",transport=lambda u:(_ for _ in ()).throw(AssertionError("must not fetch")))["ok"] is False

def test_registry_not_yet_certified():
 r=registry()
 assert any(s["id"]=="noaa-snpp-chlorophyll-monthly" and s["capability"]=="integration-pending" for s in r["sources"])
 assert next(v for v in r["variables"] if v["id"]=="chlorophyll-a")["retrieval_status"]=="not-connected"

def test_frontend_assets_exist():
 for p in ("web/index.html","web/app/index.html"):
  assert "ocean-biology-v4600.js?v=4.60.0" in (ROOT/p).read_text()
 js=(ROOT/"web/app/assets/ocean-biology-v4600.js").read_text()
 for a in ("ocean4600Fetch","ocean4600Grid","ocean4600Export","response_sha256"):assert a in js

def test_noaa_axes_and_longitude_normalization():
 calls=[]
 payload=("time,latitude,longitude,chlor_a\nUTC,degrees_north,degrees_east,mg m-3\n2026-08-01T12:00:00Z,12,295,0.14\n").encode()
 def fetch(url):
  calls.append(url)
  return payload
 response=retrieve_chlorophyll_grid(12,-65,"2026-08-01",transport=fetch)
 assert response["ok"],response
 assert response["cells"][0]["longitude"]==-65
 assert "2026-08-01T12:00:00Z" in calls[0]
 assert "12.5000" in calls[0] and "11.5000" in calls[0]
 assert "294.5000" in calls[0] and "295.5000" in calls[0]
