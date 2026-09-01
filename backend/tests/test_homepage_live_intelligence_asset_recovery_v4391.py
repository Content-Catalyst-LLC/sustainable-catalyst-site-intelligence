from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js"
PHP = ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"


def test_live_intelligence_separates_fetch_and_render_failures():
    js = JS.read_text(encoding="utf-8")
    assert "feed_render_failure" in js
    assert "renderMinimalFallback(data, error)" in js
    assert "Site Intelligence Live Intelligence fetch failed." in js
    assert "fetchJson(endpoint).then(function (data)" in js
    assert "}, function (error) {" in js


def test_live_intelligence_isolates_individual_signal_rendering():
    js = JS.read_text(encoding="utf-8")
    assert "const safeItemHtml" in js
    assert "scsi:live-intelligence-render-error" in js
    assert "filter(Boolean).join('')" in js
    assert ".trimEnd()" not in js


def test_homepage_summary_uses_schema_tolerant_metric_slots():
    js = JS.read_text(encoding="utf-8")
    php = PHP.read_text(encoding="utf-8")
    method = php.split("public function site_intelligence_home_shortcode", 1)[1].split("public function", 1)[0]
    assert "data-home-metric-slot" in method
    assert "data-home-metric=\"" not in method
    assert "metricCards" in js
    assert "CSS.escape(String(metric.id" not in js
