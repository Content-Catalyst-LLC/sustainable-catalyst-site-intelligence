#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];js=(ROOT/'backend/public_app/assets/transportation-infrastructure-v42700.js').read_text();css=(ROOT/'backend/public_app/assets/transportation-infrastructure-v42700.css').read_text();prev=(ROOT/'backend/public_app/assets/human-settlements-v42600.js').read_text()
for t in ['SCSITransportationInfrastructureV42700','TRANSPORTATION EVIDENCE','/public/transportation-infrastructure/catalog','transportationInfrastructurePanel']: assert t in js,t
assert 'loadTransportation' in prev and 'transportation-infrastructure-v42700.js' in prev
assert '.ti42700-panel' in css
print('PASS: v4.27.0 transportation direct + iframe-compatible browser asset gate')
