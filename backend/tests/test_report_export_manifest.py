from app.report_generator import bundle_manifest_report


def test_bundle_manifest_is_lightweight_report_shape():
    manifest = bundle_manifest_report([
        {"id": "site-intelligence", "endpoint": "/reports/site-intelligence", "formats": ["json", "markdown", "csv"]}
    ])
    assert manifest["ok"] is True
    assert manifest["report_id"] == "site-intelligence-export-bundle"
    assert manifest["sections"]
    assert "lightweight" in manifest["summary"].lower()
