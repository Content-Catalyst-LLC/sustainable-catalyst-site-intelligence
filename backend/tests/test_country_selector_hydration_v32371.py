from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.version import APP_VERSION


ROOT = Path(__file__).resolve().parents[2]


def test_country_catalog_contract_has_global_options():
    assert APP_VERSION == "4.34.0"
    client = TestClient(app)
    primary = client.get("/public/countries").json()
    fallback = client.get("/public/data-truth/countries").json()
    assert primary["country_count"] >= 20
    assert fallback["country_count"] >= 170
    for code in ("KEN", "BRA", "IND", "DEU", "USA"):
        assert any(item["code"] == code for item in primary["countries"])
        assert any(item["code"] == code for item in fallback["countries"])


def test_shipped_shell_hydrates_country_selector_during_startup():
    app_js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    truth_js = (ROOT / "backend/public_app/assets/data-truth-v32371.js").read_text(encoding="utf-8")
    index = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")

    assert 'apiWithRetry("/public/countries",3)' in app_js
    assert 'apiWithRetry("/public/data-truth/countries",2)' in app_js
    assert 'const countryCatalogTask=hydrateCountrySelector(initialCountry)' in app_js
    assert 'countryCatalogTask.then(code=>loadCountry(code))' in app_js
    assert 'scsi:country-catalog-ready' in app_js
    assert 'scsi:country-catalog-ready' in truth_js
    assert 'data-truth-v32371.js?v=4.34.0' in index
