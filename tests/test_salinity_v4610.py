"""v4.61 salinity contract tests with mocked NOAA ERDDAP CSV."""
from pathlib import Path
from backend.app.salinity_v4610 import retrieve_salinity_grid
from backend.app.ocean_contracts_v4590 import registry
ROOT=Path(__file__).resolve().parents[1]
def sample(day="2026-10-01",altitude="0"):
 return (f"time,altitude,latitude,longitude,sss\nUTC,m,degrees_north,degrees_east,PSU\n{day}T12:00:00Z,{altitude},12,-65,34.71\n{day}T12:00:00Z,{altitude},12.25,-64.75,NaN\n").encode()
def test_source_and_missing():
 urls=[]
 def fetch(u):urls.append(u);return sample()
 x=retrieve_salinity_grid(12,-65,"2026-10-01",transport=fetch)
 assert x["ok"] and x["unit"]=="PSU" and x["missing_count"]==1 and len(x["cells"])==1
 assert x["cells"][0]["value"]==34.71
 assert len(x["receipt"]["response_sha256"])==64
 assert "coastwatchSMOSv662SSS1day.csv" in urls[0] and "%20" not in urls[0]
 assert "sss[" in urls[0] and "[(0)]" in urls[0]
def test_wrong_day_rejected():
 assert retrieve_salinity_grid(12,-65,"2026-10-01",transport=lambda _:sample("2026-09-30"))["status"]=="unavailable"
def test_subsurface_rejected():
 assert retrieve_salinity_grid(12,-65,"2026-10-01",transport=lambda _:sample(altitude="5"))["status"]=="unavailable"
def test_invalid_coordinates_do_not_fetch():
 def fail(_):raise AssertionError("Must not contact NOAA")
 assert not retrieve_salinity_grid(90,-65,"2026-10-01",transport=fail)["ok"]
def test_registry_remains_honest():
 data=registry()
 assert next(v for v in data["variables"] if v["id"]=="sea-surface-salinity")["retrieval_status"]=="not-connected"
 assert next(s for s in data["sources"] if s["id"]=="noaa-smos-daily-salinity")["capability"]=="integration-pending"
def test_frontend_registered():
 for p in ("web/index.html","web/app/index.html"):
  assert "ocean-salinity-v4610.js?v=4.61.0" in (ROOT/p).read_text()
 script=(ROOT/"web/app/assets/ocean-salinity-v4610.js").read_text()
 for x in ("sal4610Date","sal4610Lat","sal4610Lon","sal4610Export","sal4610Map"):assert x in script
