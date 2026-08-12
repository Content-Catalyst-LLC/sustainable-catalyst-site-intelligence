#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
index = (ROOT / 'backend/public_app/index.html').read_text()
app = (ROOT / 'backend/public_app/assets/app.js').read_text()
main = (ROOT / 'backend/app/main.py').read_text()

assert 'data-scsi-release="4.35.20"' in index
assert 'EXTERNAL RESILIENCE · v4.35.20' in index
for marker in ('externalResilienceStatus', 'resiliencePolicyMetric', 'resilienceCacheMetric', 'resilienceRetryMetric', 'resilienceCircuitMetric'):
    assert marker in index, marker
for marker in ('renderExternalResilience', '/public/external-resilience', 'upstream health is non-blocking for deployment'):
    assert marker in app, marker
for endpoint in ('/public/external-resilience', '/public/external-resilience/readiness', '/public/external-resilience/providers'):
    assert endpoint in main, endpoint
assert len(index.encode()) <= 170_000
assert len(app.encode()) <= 260_000
print('PASS: v4.35.20 external resilience browser/static gate')
