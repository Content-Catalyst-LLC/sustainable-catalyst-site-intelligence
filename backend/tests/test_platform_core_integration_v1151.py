from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.platform_core_integration import (
    CoreSettings,
    PlatformCoreClient,
    content_hash,
    stable_id,
)

client = TestClient(app)


def test_root_reports_v1151():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "1.15.2"


def test_stable_ids_are_deterministic():
    first = stable_id("evidence", "KEN", "SP.POP.TOTL", 2023, 123)
    second = stable_id("evidence", "KEN", "SP.POP.TOTL", 2023, 123)
    assert first == second
    assert first.startswith("sc:evidence:")


def test_content_hash_is_canonical():
    assert content_hash({"b": 2, "a": 1}) == content_hash({"a": 1, "b": 2})


def test_public_status_never_returns_keys(monkeypatch):
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_ENABLED", "true")
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_URL", "https://core.example")
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_WRITE_API_KEY", "do-not-expose")
    response = client.get("/public/platform-core/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["write_key_configured"] is True
    assert "do-not-expose" not in response.text


def test_queue_on_transport_failure(tmp_path):
    settings = CoreSettings(
        enabled=True,
        base_url="https://core.invalid",
        write_api_key="test",
        public_api_key="",
        timeout_seconds=1,
        queue_path=str(tmp_path / "queue.jsonl"),
        public_evidence_base_url="",
    )
    client_instance = PlatformCoreClient(settings)
    with patch.object(client_instance, "_request", side_effect=OSError("offline")):
        result, state = client_instance.post_or_queue("/v1/source-snapshots", {"id": "x"})
    assert result is None
    assert state == "queued"
    assert Path(settings.queue_path).exists()


def test_record_indicator_lineage_uses_core_contracts(tmp_path):
    settings = CoreSettings(
        enabled=True,
        base_url="https://core.example",
        write_api_key="test",
        public_api_key="",
        timeout_seconds=2,
        queue_path=str(tmp_path / "queue.jsonl"),
        public_evidence_base_url="https://core.example",
    )
    client_instance = PlatformCoreClient(settings)
    calls = []

    def fake_post(path, payload):
        calls.append((path, payload))
        return {"id": payload.get("id")}, "recorded"

    with patch.object(client_instance, "post_or_queue", side_effect=fake_post):
        lineage = client_instance.record_indicator_lineage(
            country_code="KEN",
            country_name="Kenya",
            indicator_id="SP.POP.TOTL",
            indicator_key="population",
            indicator_label="Population",
            canonical_url="https://api.worldbank.org/test",
            retrieved_at="2026-07-10T00:00:00+00:00",
            raw_payload=[{"test": True}],
            latest={"year": 2023, "value": 55_000_000, "unit": "people"},
            series=[{"year": 2023, "value": 55_000_000}],
        )

    paths = [item[0] for item in calls]
    assert "/v1/source-snapshots" in paths
    assert "/v1/provenance/activities" in paths
    assert "/v1/evidence-records" in paths
    assert any("/links" in path for path in paths)
    assert lineage["evidence_id"].startswith("sc:evidence:")
    assert lineage["source_snapshot_id"].startswith("sc:snapshot:")


def test_evidence_drawer_assets_present():
    base = Path(__file__).resolve().parents[1] / "public_app"
    assert "evidenceDrawer" in (base / "index.html").read_text()
    assert "openEvidenceDrawer" in (base / "assets" / "app.js").read_text()
    assert "evidence-drawer" in (base / "assets" / "app.css").read_text()
