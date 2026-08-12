#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/'backend/public_app/index.html').read_text(); app=(ROOT/'backend/public_app/assets/app.js').read_text(); main=(ROOT/'backend/app/main.py').read_text()
assert 'data-scsi-release="4.35.18"' in index
assert 'Production controls ready' in app
for endpoint in ('/public/authoritative-connectors/gdacs/events','/public/humanitarian/live/gdacs','/public/authoritative-connectors/hdx/datasets','/public/humanitarian/discovery/hdx','/public/authoritative-connectors/hdx-hapi','/public/food-security/live/hdx-hapi','/public/authoritative-connectors/ipc','/public/food-security/live/ipc','/public/authoritative-connectors/fews-net','/public/food-security/live/fews-net'):
    assert endpoint in main,endpoint
print('PASS: v4.35.18 Agriculture/Food Security/Humanitarian workspace connector closure browser/static gate')
