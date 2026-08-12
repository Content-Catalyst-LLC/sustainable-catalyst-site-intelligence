#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/'backend/public_app/index.html').read_text()
app=(ROOT/'backend/public_app/assets/app.js').read_text()
main=(ROOT/'backend/app/main.py').read_text()
truth=(ROOT/'backend/public_app/assets/record-provenance-v3238.js').read_text()
promotion=(ROOT/'promote_site_intelligence_v4_35_7_to_github_and_render_macos.sh').read_text()
assert 'data-scsi-release="4.35.23"' in index
assert 'EVIDENCE INTELLIGENCE · v4.35.23' in index
assert 'evidenceIntelligenceStatus' in index and 'renderEvidenceIntelligence' in app
assert '/public/evidence-intelligence' in app
for endpoint in ('/public/evidence-intelligence','/public/evidence-intelligence/metrics','/public/evidence-intelligence/precedence','/public/evidence-intelligence/freshness','/public/evidence-intelligence/indicator/{indicator_id}','/public/evidence-intelligence/select','/public/evidence-intelligence/readiness'): assert endpoint in main,endpoint
assert "field('Freshness',record.freshness?.status)" in truth
assert "field('Metric concept',record.semantics?.concept_id)" in truth
assert 'Deep gate:' not in promotion
for forbidden in ('/public/climate/state','/public/biodiversity/state','/public/mining-critical-materials/state','/public/exoplanet-habitability/state'): assert forbidden not in promotion
print('PASS: v4.35.23 evidence-intelligence browser/static gate')
