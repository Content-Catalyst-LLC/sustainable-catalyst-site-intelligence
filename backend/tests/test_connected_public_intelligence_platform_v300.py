from fastapi.testclient import TestClient

from app.main import app
from app.version import APP_VERSION, RELEASE_NAME

client = TestClient(app)


def test_v300_version_and_release_name():
    assert APP_VERSION == "3.1.2"
    assert RELEASE_NAME == "Connected Public Intelligence and Evidence Platform"
    build = client.get("/public/build-info")
    assert build.status_code == 200
    assert build.json()["version"] == "3.1.2"
    assert build.json()["release_name"] == RELEASE_NAME


def test_connected_platform_overview_is_public_and_account_free():
    response = client.get("/public/connected-intelligence")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "3.1.2"
    assert payload["record_count"] >= 50
    assert payload["public_access_requires_account"] is False
    assert payload["governance"]["private_runtime_records_exposed"] is False
    assert "site-intelligence" in payload["platforms"]
    assert "platform-core" in payload["platforms"]


def test_connected_search_covers_sources_datasets_and_routes():
    response = client.get("/public/connected-intelligence/search", params={"q": "NASA"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert any(item["record_type"] in {"source", "dataset", "spatial-layer"} for item in payload["results"])
    assert "not evidence quality" in payload["inference_note"].lower()


def test_empty_search_does_not_dump_catalog():
    payload = client.get("/public/connected-intelligence/search", params={"q": ""}).json()
    assert payload["count"] == 0
    assert payload["results"] == []


def test_context_and_provenance_are_digest_linked():
    search = client.get("/public/connected-intelligence/search", params={"q": "NASA", "limit": 1}).json()
    record_id = search["results"][0]["record_id"]
    context = client.get(f"/public/connected-intelligence/context/{record_id}")
    assert context.status_code == 200
    payload = context.json()
    assert payload["record"]["record_id"] == record_id
    assert payload["provenance"]["verified"] is True
    assert len(payload["provenance"]["chain"]) == 3


def test_unknown_context_is_404():
    assert client.get("/public/connected-intelligence/context/not-a-real-record").status_code == 404


def test_lifecycle_preserves_human_review():
    payload = client.get("/public/connected-intelligence/lifecycle").json()
    ids = [item["id"] for item in payload["stages"]]
    assert ids == ["source", "ingest", "archive", "harmonize", "analyze", "review", "publish", "monitor", "exchange"]
    assert all(item["automatic_publication"] is False for item in payload["stages"])


def test_public_diagnostics_do_not_claim_persistent_search_cluster():
    payload = client.get("/public/connected-intelligence/diagnostics").json()
    assert payload["persistent_search_service_claimed"] is False
    assert payload["runtime_indexing"] == "approved-public-records-only"


def test_connected_export_json_and_csv():
    response = client.get("/public/connected-intelligence/export", params={"q": "climate", "format": "json"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert "sha256" in response.json()
    csv_response = client.get("/public/connected-intelligence/export", params={"q": "climate", "format": "csv"})
    assert csv_response.status_code == 200
    assert "record_id,record_type,title" in csv_response.text


def test_admin_control_center_is_available_in_development():
    response = client.get("/admin/connected-intelligence/control-center")
    assert response.status_code == 200
    payload = response.json()
    assert payload["remote_write_performed"] is False
    assert payload["index_preview"]["write_performed"] is False
