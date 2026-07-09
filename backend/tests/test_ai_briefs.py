from app.ai_briefs import ai_status, build_ai_brief, deterministic_brief


class DummySettings:
    ai_provider = "disabled"
    gemini_api_key = ""
    gemini_model = "gemini-1.5-flash"
    ai_temperature = 0.2
    ai_max_output_tokens = 1200
    ai_timeout_seconds = 12


def sample_report():
    return {
        "ok": True,
        "report_id": "site-intelligence",
        "title": "Weekly Site Intelligence Report",
        "summary": "A planning report for Sustainable Catalyst.",
        "generated_at": "2026-07-09T00:00:00Z",
        "source": "demo",
        "date_range": {"start_date": "28daysAgo", "end_date": "today"},
        "highlights": ["1,000 page views in the reviewed period."],
        "recommendations": ["Improve internal links from article maps."],
        "sections": [{"section_id": "top_pages", "title": "Top pages", "rows": [{"title": "Research Library", "summary": "High visibility page."}]}],
        "methodology": {"summary": "Directional planning report.", "privacy_note": "Internal planning only."},
    }


def test_ai_status_disabled_by_default():
    status = ai_status(DummySettings())
    assert status["enabled"] is False
    assert status["provider"] == "disabled"
    assert status["mode"] == "deterministic-fallback"


def test_deterministic_brief_shape():
    brief = deterministic_brief(sample_report(), "site-intelligence")
    assert brief["ok"] is True
    assert brief["brief_id"] == "site-intelligence-ai-brief"
    assert brief["executive_summary"]
    assert brief["recommended_actions"]
    assert brief["public_safe_summary"]


def test_build_ai_brief_falls_back_when_disabled():
    brief = build_ai_brief(sample_report(), "site-intelligence", DummySettings(), use_ai=True)
    assert brief["provider"] == "disabled"
    assert brief["ai_status"]["enabled"] is False
    assert "deterministic" in brief["methodology"]["summary"].lower()
