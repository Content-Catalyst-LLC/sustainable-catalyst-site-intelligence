from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.version import APP_VERSION

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "backend" / "public_app" / "assets"
WP = ROOT / "wordpress-plugin" / "sustainable-catalyst-site-intelligence" / "assets"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_v4361_release_identity_and_openapi_recovers():
    assert APP_VERSION == "4.36.1"
    schema = app.openapi()
    assert schema["info"]["version"] == "4.36.1"
    for route in (
        "/public/authoritative-connectors/noaa-erddap/search",
        "/public/authoritative-connectors/noaa-coops/data",
        "/public/authoritative-connectors/obis/occurrences",
        "/public/authoritative-connectors/nasa-exoplanets",
        "/public/authoritative-connectors/nasa-cmr/collections",
    ):
        assert route in schema["paths"]

    response = TestClient(app).get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["version"] == "4.36.1"


def test_openapi_forward_reference_regression_is_removed():
    main = read(ROOT / "backend" / "app" / "main.py")
    assert "request: Dict[str, Any]" not in main
    assert main.count("request: dict[str, Any] = Body(default={})") >= 2


def test_ocean_surface_binds_noaa_erddap_live_evidence():
    js = read(PUBLIC / "ocean-surface-v4500.js")
    assert "/public/authoritative-connectors/noaa-erddap/search" in js
    assert "LIVE AUTHORITATIVE EVIDENCE" in js
    assert "live dataset records" in js
    assert "Coverage at point/time" in js


def test_marine_biodiversity_binds_obis_live_occurrences():
    js = read(PUBLIC / "marine-biodiversity-v4900.js")
    assert "/public/authoritative-connectors/obis/occurrences" in js
    assert "IOC-UNESCO OBIS API v3" in js
    assert "Zero records do not establish species absence" in js


def test_coastal_change_binds_noaa_coops_station_evidence():
    js = read(PUBLIC / "coastal-change-v41400.js")
    assert "/public/authoritative-connectors/noaa-coops/data" in js
    assert "NOAA CO-OPS DATA API" in js
    assert "datum-specific" in js


def test_space_binds_nasa_exoplanet_and_cmr_records():
    exo = read(PUBLIC / "exoplanet-habitability-v43500.js")
    planetary = read(PUBLIC / "planetary-intelligence-v4200.js")
    assert "/public/exoplanet-habitability/live" in exo
    assert "NASA EXOPLANET ARCHIVE TAP" in exo
    assert "Equilibrium temperature is not surface temperature" in exo
    assert "/public/authoritative-connectors/nasa-cmr/collections" in planetary
    assert "NASA EOSDIS CMR" in planetary
    assert "not itself a planetary observation value" in planetary


def test_changed_browser_assets_match_wordpress_plugin_copies():
    for name in (
        "ocean-surface-v4500.js",
        "ocean-surface-v4500.css",
        "marine-biodiversity-v4900.js",
        "marine-biodiversity-v4900.css",
        "coastal-change-v41400.js",
        "coastal-change-v41400.css",
        "exoplanet-habitability-v43500.js",
        "exoplanet-habitability-v43500.css",
        "planetary-intelligence-v4200.js",
        "planetary-intelligence-v4200.css",
    ):
        assert (PUBLIC / name).read_bytes() == (WP / name).read_bytes(), name
