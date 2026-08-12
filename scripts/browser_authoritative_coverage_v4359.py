#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/'backend/public_app/index.html').read_text()
app=(ROOT/'backend/public_app/assets/app.js').read_text()
main=(ROOT/'backend/app/main.py').read_text()
assert 'data-scsi-release="4.35.23"' in index
assert 'Production controls ready' in app
for endpoint in ('/public/authoritative-apis/production-audit','/public/authoritative-apis/closure-ledger','/public/authoritative-apis/production-readiness'):
 assert endpoint in main,endpoint
print('PASS: v4.35.23 authoritative coverage browser/static gate')
