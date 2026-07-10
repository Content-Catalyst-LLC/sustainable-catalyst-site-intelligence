from app.config import Settings
from app.sustainable_development_connectors import (
    CONNECTOR_RESPONSE_SCHEMA,
    classify_freshness,
    connector_cache_status,
    connector_reliability,
    freshness_policy,
    schema_validation_report,
    validate_observation,
)


def sample_record():
    return {
        "source_id": "nasa-power",
        "indicator_id": "T2M",
        "geography": {"type": "point", "latitude": 41.8781, "longitude": -87.6298},
        "period": "2026-07-10",
        "value": 24.2,
        "unit": "celsius",
        "freshness": "recent",
        "observation_type": "observed",
        "retrieved_at": "2026-07-10T00:00:00+00:00",
        "is_derived": False,
    }


def test_observation_schema_validation():
    result = validate_observation(sample_record())
    assert result["ok"] is True
    broken = sample_record()
    del broken["unit"]
    assert validate_observation(broken)["ok"] is False


def test_registry_schema_report_and_response_schema():
    report = schema_validation_report()
    assert report["ok"] is True
    assert report["sample_validation"]["ok"] is True
    assert CONNECTOR_RESPONSE_SCHEMA["schema"].endswith("/1.1")


def test_network_safe_reliability_and_cache_status():
    settings = Settings(sustainable_development_live_checks=False)
    report = connector_reliability(settings, live=False)
    assert report["live_checks"] is False
    assert len(report["connectors"]) >= 9
    assert all(row["status"] == "configured" for row in report["connectors"])
    assert connector_cache_status()["ok"] is True


def test_freshness_policy_and_unknown_timestamp():
    policy = freshness_policy()
    assert len(policy["thresholds"]) >= 9
    assert classify_freshness("daily", None) == "unknown"
