#!/usr/bin/env python3
"""Static and API contract validation for Site Intelligence v4.15.0."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)

schema = client.get("/public/workspaces/unified-state")
assert schema.status_code == 200, schema.text
payload = schema.json()
assert payload["ok"] is True
assert payload["version"] == "4.15.0"
assert payload["contract"] == "unified-analytical-workspace-state"
assert payload["route_count"] == 6
assert payload["country_catalog_count"] >= 170

normalized = client.post(
    "/public/workspaces/unified-state/normalize",
    json={"view": "compare", "country": "BRA", "compare": "IND", "indicator": "population"},
)
assert normalized.status_code == 200, normalized.text
body = normalized.json()
assert body["state"]["country"] == "BRA"
assert body["state"]["compare"] == "IND"
assert len(body["fingerprint"]) == 64

handoff = client.post(
    "/public/workspaces/unified-state/handoff/earth",
    json={"view": "compare", "country": "BRA", "compare": "IND", "layer_id": "vegetation-index"},
)
assert handoff.status_code == 200, handoff.text
body = handoff.json()
assert body["target"] == "earth"
assert body["state"]["country"] == "BRA"
assert "view=earth" in body["path"]
assert body["snapshot"] is False

html = (BACKEND / "public_app" / "index.html").read_text(encoding="utf-8")
worker = (BACKEND / "public_app" / "service-worker.js").read_text(encoding="utf-8")
js = (BACKEND / "public_app" / "assets" / "cross-view-state-v3250.js").read_text(encoding="utf-8")
assert 'data-scsi-release="4.15.0"' in html
assert "cross-view-state-v3250.css?v=4.15.0" in html
assert "cross-view-state-v3250.js?v=4.15.0" in html
assert "cross-view-state-v3250.js" in worker
assert "SiteIntelligenceCrossViewState" in js
assert "scsi:cross-view-ready" in js

policy = json.loads((BACKEND / "data" / "unified_analytical_state_policy_v3250.json").read_text(encoding="utf-8"))
assert policy["version"] == "4.15.0"
assert set(policy["routes"]) == {"overview", "global", "country", "compare", "spatial", "earth"}

print(
    json.dumps(
        {
            "version": payload["version"],
            "route_count": payload["route_count"],
            "country_catalog_count": payload["country_catalog_count"],
            "normalized_fingerprint": normalized.json()["fingerprint"],
            "handoff_path": handoff.json()["path"],
            "asset": "cross-view-state-v3250.js",
        },
        indent=2,
    )
)
print("PASS: Site Intelligence v4.15.0 unified analytical state contracts are complete.")
