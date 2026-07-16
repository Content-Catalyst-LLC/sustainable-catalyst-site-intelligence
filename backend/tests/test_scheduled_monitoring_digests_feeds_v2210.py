from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.config import Settings, get_settings
from app.main import app
from app.scheduled_monitoring_v2210 import ScheduledMonitoringCenter, SCHEMA_VERSION


def settings(tmp_path: Path) -> Settings:
    root = tmp_path / "monitoring"
    return Settings(
        scheduled_monitoring_root_path=str(root),
        scheduled_monitoring_monitors_path=str(root / "monitors.jsonl"),
        scheduled_monitoring_checks_path=str(root / "checks.jsonl"),
        scheduled_monitoring_alerts_path=str(root / "alerts.jsonl"),
        scheduled_monitoring_digests_path=str(root / "digests.jsonl"),
        scheduled_monitoring_deliveries_path=str(root / "deliveries.jsonl"),
        scheduled_monitoring_feeds_path=str(root / "feeds.jsonl"),
        scheduled_monitoring_policy_path=str(Path(__file__).resolve().parents[1] / "data/scheduled_monitoring_policy_v2210.json"),
        scheduled_monitoring_dedupe_hours=72,
    )


def signal(signal_id: str = "signal:1", value: float = 8.0):
    return {
        "signal_id": signal_id,
        "family": "science",
        "source_id": "source:nasa",
        "countries": ["USA"],
        "value_number": value,
        "observed_at": "2026-07-16T10:00:00+00:00",
        "title": "Observed environmental change",
        "summary": "Public source record.",
        "freshness": "current",
    }


def center(tmp_path: Path, now: datetime | None = None) -> ScheduledMonitoringCenter:
    stamp = now or datetime(2026, 7, 16, 12, tzinfo=timezone.utc)
    return ScheduledMonitoringCenter(settings(tmp_path), now_fn=lambda: stamp)


def monitor(center: ScheduledMonitoringCenter, **overrides):
    request = {
        "monitor_id": "monitor:science",
        "title": "Science change monitor",
        "summary": "Watch public science records.",
        "cadence": "daily",
        "visibility": "public",
        "families": ["science"],
        "countries": ["USA"],
        "rules": [{"id": "rule:threshold", "name": "Threshold", "family": "science", "threshold_operator": "gte", "threshold_value": 5}],
        "channels": ["feed"],
    }
    request.update(overrides)
    return center.save_monitor(request)["monitor"]


def test_monitor_registry_due_schedule_and_public_boundary(tmp_path):
    c = center(tmp_path)
    row = monitor(c)
    assert row["cadence"] == "daily"
    assert c.due_monitors()[0]["monitor_id"] == row["monitor_id"]
    public = c.public_summary()
    assert public["schema"] == SCHEMA_VERSION
    assert public["hosted_profile_required"] is False
    assert "rules" not in public["monitors"][0]


def test_check_deduplicates_repeated_alerts(tmp_path):
    c = center(tmp_path)
    monitor(c)
    first = c.check_monitor("monitor:science", {"signals": [signal()]})
    second = c.check_monitor("monitor:science", {"signals": [signal()]})
    assert first["receipt"]["new_alert_count"] == 1
    assert second["receipt"]["new_alert_count"] == 0
    assert second["duplicates_suppressed"] == 1
    assert first["new_alerts"][0]["operational_emergency_alert"] is False


def test_changed_signal_creates_new_alert(tmp_path):
    c = center(tmp_path)
    monitor(c)
    c.check_monitor("monitor:science", {"signals": [signal(value=8)]})
    result = c.check_monitor("monitor:science", {"signals": [signal(value=9)]})
    assert result["receipt"]["new_alert_count"] == 1


def test_run_due_is_dry_run_by_default(tmp_path):
    c = center(tmp_path)
    monitor(c)
    preview = c.run_due()
    assert preview["dry_run"] is True
    assert preview["due_count"] == 1
    assert preview["persistent_scheduler_active"] is False


def test_daily_digest_is_deterministic_and_draft(tmp_path):
    c = center(tmp_path)
    monitor(c)
    c.check_monitor("monitor:science", {"signals": [signal()]})
    digest = c.generate_digest({"period": "daily", "monitor_ids": ["monitor:science"], "visibility": "public"})["digest"]
    assert digest["status"] == "draft"
    assert digest["alert_count"] == 1
    assert digest["group_count"] == 1
    assert digest["ai_generated"] is False
    assert digest["automatic_publication"] is False
    assert digest["digest_sha256"]


def test_digest_publication_requires_human_confirmation(tmp_path):
    c = center(tmp_path)
    monitor(c)
    digest = c.generate_digest({"period": "daily", "visibility": "public"})["digest"]
    with pytest.raises(ValueError, match="human_confirmed"):
        c.approve_digest(digest["digest_id"], {"action": "publish"})
    published = c.approve_digest(digest["digest_id"], {"action": "publish", "human_confirmed": True, "reviewer": "Editor"})["digest"]
    assert published["status"] == "published"
    assert c.digests(public=True)[0]["digest_id"] == digest["digest_id"]


def test_json_rss_and_atom_feeds_require_no_subscriber_profile(tmp_path):
    c = center(tmp_path)
    monitor(c)
    digest = c.generate_digest({"period": "daily", "monitor_ids": ["monitor:science"], "visibility": "public"})["digest"]
    c.approve_digest(digest["digest_id"], {"action": "publish", "human_confirmed": True})
    feed = c.save_feed({"feed_id": "feed:science", "title": "Science feed", "description": "Public source changes", "monitor_ids": ["monitor:science"]})["feed"]
    assert feed["hosted_profile_required"] is False
    for fmt, media in [("json", "application/json"), ("rss", "application/rss+xml"), ("atom", "application/atom+xml")]:
        media_type, body = c.feed_payload("feed:science", fmt)
        assert media_type == media
        assert "Science feed" in body
        assert digest["title"] in body


def test_delivery_logs_feed_and_disables_optional_adapters(tmp_path):
    c = center(tmp_path)
    monitor(c)
    digest = c.generate_digest({"period": "daily", "monitor_ids": ["monitor:science"], "visibility": "public"})["digest"]
    c.approve_digest(digest["digest_id"], {"action": "publish", "human_confirmed": True})
    feed = c.deliver_digest(digest["digest_id"], {"channel": "feed"})["delivery"]
    email = c.deliver_digest(digest["digest_id"], {"channel": "email"})["delivery"]
    assert feed["state"] == "published"
    assert email["state"] == "skipped"
    assert email["recipient_or_url"] == "[redacted]"
    assert email["conversation_data_shared"] is False


def test_quiet_hours_defer_optional_delivery(tmp_path):
    c = center(tmp_path, datetime(2026, 7, 16, 23, tzinfo=timezone.utc))
    monitor(c, channels=["webhook"], quiet_hours_utc={"start": 22, "end": 7})
    digest = c.generate_digest({"period": "daily", "monitor_ids": ["monitor:science"], "visibility": "public"})["digest"]
    c.approve_digest(digest["digest_id"], {"action": "publish", "human_confirmed": True})
    delivery = c.deliver_digest(digest["digest_id"], {"channel": "webhook"})["delivery"]
    assert delivery["state"] == "deferred"
    assert "quiet" in delivery["detail"].lower()


def test_public_and_admin_routes(tmp_path):
    cfg = settings(tmp_path)
    app.dependency_overrides[get_settings] = lambda: cfg
    try:
        client = TestClient(app)
        assert client.get("/public/scheduled-monitoring").status_code == 200
        assert client.get("/public/scheduled-monitoring/diagnostics").json()["persistent_scheduler_active"] is False
        created = client.post("/admin/scheduled-monitoring/monitors", json={
            "monitor_id": "monitor:route", "title": "Route monitor", "cadence": "daily", "visibility": "public",
            "rules": [{"id": "r", "name": "Rule", "family": "science", "threshold_operator": "gte", "threshold_value": 1}],
        })
        assert created.status_code == 200
        checked = client.post("/admin/scheduled-monitoring/monitors/monitor:route/check", json={"signals": [signal("route-signal")]})
        assert checked.status_code == 200
        digest = client.post("/admin/scheduled-monitoring/digests", json={"period": "daily", "monitor_ids": ["monitor:route"], "visibility": "public"}).json()["digest"]
        assert client.get("/public/intelligence-digests").json()["digests"] == []
        assert client.post(f"/admin/scheduled-monitoring/digests/{digest['digest_id']}/review", json={"action": "publish", "human_confirmed": True}).status_code == 200
        assert client.post("/admin/scheduled-monitoring/feeds", json={"feed_id": "feed:route", "title": "Route feed", "monitor_ids": ["monitor:route"]}).status_code == 200
        assert client.get("/public/intelligence-feeds/feed:route?format=rss").headers["content-type"].startswith("application/rss+xml")
        assert client.get("/admin/scheduled-monitoring/control-center").status_code == 200
    finally:
        app.dependency_overrides.clear()
